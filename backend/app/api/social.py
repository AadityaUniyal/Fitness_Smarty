from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from app.database import get_db
from app import schemas, models
from app.auth import get_current_user

router = APIRouter(prefix="/api/social", tags=["Social Feed"])


def _user_name(user: models.EnhancedUser) -> str:
    return user.full_name or user.username or f"User {user.id}"


def _user_avatar(user: models.EnhancedUser) -> str:
    name = _user_name(user)
    parts = name.split()
    return (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()[:2]


@router.get("/posts", response_model=schemas.SocialFeedResponse)
def get_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    following_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    query = db.query(models.SocialPost)
    if following_only:
        followed = db.query(models.SocialFollow.following_id).filter(
            models.SocialFollow.follower_id == current_user.id
        ).subquery()
        query = query.filter(models.SocialPost.user_id.in_(followed))
    total = query.count()
    posts = query.order_by(desc(models.SocialPost.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    liked_post_ids = {l.post_id for l in db.query(models.SocialLike).filter(
        models.SocialLike.user_id == current_user.id,
        models.SocialLike.post_id.in_([p.id for p in posts]),
    ).all()}
    result = []
    for p in posts:
        user = db.query(models.EnhancedUser).filter(models.EnhancedUser.id == p.user_id).first()
        result.append(schemas.SocialPostResponse(
            id=p.id, user_id=p.user_id,
            user_name=_user_name(user) if user else "Unknown",
            user_avatar=_user_avatar(user) if user else "??",
            text=p.text, post_type=p.post_type,
            workout_data=p.workout_data, achievement_data=p.achievement_data,
            image_url=p.image_url,
            like_count=len(p.likes), comment_count=len(p.comments),
            is_liked=p.id in liked_post_ids,
            created_at=p.created_at,
        ))
    return schemas.SocialFeedResponse(posts=result, total_count=total, page=page, page_size=page_size)


@router.post("/posts", response_model=schemas.SocialPostResponse, status_code=201)
def create_post(
    data: schemas.SocialPostCreate,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    post = models.SocialPost(
        user_id=current_user.id, text=data.text, post_type=data.post_type,
        workout_data=data.workout_data, achievement_data=data.achievement_data,
        image_url=data.image_url,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return schemas.SocialPostResponse(
        id=post.id, user_id=post.user_id,
        user_name=_user_name(current_user), user_avatar=_user_avatar(current_user),
        text=post.text, post_type=post.post_type,
        workout_data=post.workout_data, achievement_data=post.achievement_data,
        image_url=post.image_url, like_count=0, comment_count=0, is_liked=False,
        created_at=post.created_at,
    )


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    post = db.query(models.SocialPost).filter(models.SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(403, "Not your post")
    db.delete(post)
    db.commit()


@router.post("/posts/{post_id}/like")
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    post = db.query(models.SocialPost).filter(models.SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    existing = db.query(models.SocialLike).filter(
        models.SocialLike.post_id == post_id,
        models.SocialLike.user_id == current_user.id,
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"liked": False, "like_count": len(post.likes) - 1}
    db.add(models.SocialLike(post_id=post_id, user_id=current_user.id))
    db.commit()
    return {"liked": True, "like_count": len(post.likes) + 1}


@router.get("/posts/{post_id}/comments", response_model=List[schemas.SocialCommentResponse])
def get_comments(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    post = db.query(models.SocialPost).filter(models.SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    comments = db.query(models.SocialComment).filter(
        models.SocialComment.post_id == post_id
    ).order_by(models.SocialComment.created_at).all()
    result = []
    for c in comments:
        user = db.query(models.EnhancedUser).filter(models.EnhancedUser.id == c.user_id).first()
        result.append(schemas.SocialCommentResponse(
            id=c.id, post_id=c.post_id, user_id=c.user_id,
            user_name=_user_name(user) if user else "Unknown",
            user_avatar=_user_avatar(user) if user else "??",
            text=c.text, created_at=c.created_at,
        ))
    return result


@router.post("/posts/{post_id}/comments", response_model=schemas.SocialCommentResponse, status_code=201)
def create_comment(
    post_id: int,
    data: schemas.SocialCommentCreate,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    post = db.query(models.SocialPost).filter(models.SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    comment = models.SocialComment(post_id=post_id, user_id=current_user.id, text=data.text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return schemas.SocialCommentResponse(
        id=comment.id, post_id=comment.post_id, user_id=comment.user_id,
        user_name=_user_name(current_user), user_avatar=_user_avatar(current_user),
        text=comment.text, created_at=comment.created_at,
    )


@router.get("/following")
def get_following(
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    follows = db.query(models.SocialFollow).filter(
        models.SocialFollow.follower_id == current_user.id
    ).all()
    users = db.query(models.EnhancedUser).filter(
        models.EnhancedUser.id.in_([f.following_id for f in follows])
    ).all()
    return [{"id": u.id, "name": _user_name(u), "avatar": _user_avatar(u)} for u in users]


@router.post("/follow/{target_id}")
def toggle_follow(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    if target_id == current_user.id:
        raise HTTPException(400, "Cannot follow yourself")
    target = db.query(models.EnhancedUser).filter(models.EnhancedUser.id == target_id).first()
    if not target:
        raise HTTPException(404, "User not found")
    existing = db.query(models.SocialFollow).filter(
        models.SocialFollow.follower_id == current_user.id,
        models.SocialFollow.following_id == target_id,
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"following": False}
    db.add(models.SocialFollow(follower_id=current_user.id, following_id=target_id))
    db.commit()
    return {"following": True}


@router.get("/users")
def get_users(
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    users = db.query(models.EnhancedUser).filter(
        models.EnhancedUser.id != current_user.id
    ).all()
    return [{"id": u.id, "name": _user_name(u), "avatar": _user_avatar(u), "full_name": u.full_name or u.username} for u in users]
