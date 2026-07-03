import React, { useState, useEffect } from 'react';
import { Heart, MessageCircle, Share2, Plus, Image, Dumbbell, Trophy, Zap, Send, MoreHorizontal, User, ChevronDown, Flame } from 'lucide-react';

const STORAGE_POSTS = 'smarty_social_posts';
const STORAGE_FOLLOWING = 'smarty_social_following';
const STORAGE_LIKES = 'smarty_social_likes';

interface Comment { id: string; userId: string; userName: string; text: string; timestamp: string; }
interface Post { id: string; userId: string; userName: string; userAvatar: string; text: string; image?: string; type: 'status' | 'workout' | 'achievement' | 'progress'; workoutData?: any; achievementData?: any; timestamp: string; comments: Comment[]; }

const FRIENDS = [
  { id: 'friend_1', name: 'Alex Chen', avatar: 'AC', bio: 'Marathon runner · 42 completed', color: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' },
  { id: 'friend_2', name: 'Sarah Kim', avatar: 'SK', bio: 'Yoga enthusiast · Strength training', color: 'text-purple-400 border-purple-500/30 bg-purple-500/10' },
  { id: 'friend_3', name: 'Marcus Jones', avatar: 'MJ', bio: 'Bodybuilding · 95kg bench', color: 'text-amber-400 border-amber-500/30 bg-amber-500/10' },
  { id: 'friend_4', name: 'Emma Wilson', avatar: 'EW', bio: 'CrossFit · Nutrition coach', color: 'text-rose-400 border-rose-500/30 bg-rose-500/10' },
  { id: 'friend_5', name: 'James Park', avatar: 'JP', bio: 'Triathlon · 10k runner', color: 'text-blue-400 border-blue-500/30 bg-blue-500/10' },
];

const DEMO_POSTS: Post[] = [
  { id: 'demo_1', userId: 'friend_1', userName: 'Alex Chen', userAvatar: 'AC', text: 'Just crushed a 10K run! New personal best at 47:32. The morning training is really paying off.', type: 'workout', workoutData: { type: 'Running', duration: 48, calories: 620, distance: '10K' }, timestamp: new Date(Date.now() - 3600000 * 2).toISOString(), comments: [] },
  { id: 'demo_2', userId: 'friend_2', userName: 'Sarah Kim', userAvatar: 'SK', text: 'Hit 100 days streak on SMARTY today! Consistency over intensity 🔥', type: 'achievement', achievementData: { name: '100 Day Streak', icon: '🔥' }, timestamp: new Date(Date.now() - 3600000 * 5).toISOString(), comments: [] },
  { id: 'demo_3', userId: 'friend_3', userName: 'Marcus Jones', userAvatar: 'MJ', text: 'New PR on deadlift: 180kg × 5. Form felt solid. Progress is real.', type: 'workout', workoutData: { type: 'Strength', duration: 75, calories: 480, exercise: 'Deadlift 180kg' }, timestamp: new Date(Date.now() - 3600000 * 8).toISOString(), comments: [] },
  { id: 'demo_4', userId: 'friend_4', userName: 'Emma Wilson', userAvatar: 'EW', text: 'Down 8kg in 6 weeks! Trust the process. Meal prep is the secret weapon.', type: 'progress', timestamp: new Date(Date.now() - 86400000).toISOString(), comments: [] },
  { id: 'demo_5', userId: 'friend_5', userName: 'James Park', userAvatar: 'JP', text: 'Recovery day — 45min zone 2 cycling and lots of stretching. Listening to your body is key.', type: 'status', timestamp: new Date(Date.now() - 86400000 * 1.5).toISOString(), comments: [] },
];

function generateId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 8); }
function timeAgo(ts: string) { const s = Math.floor((Date.now() - new Date(ts).getTime()) / 1000); if (s < 60) return 'just now'; const m = Math.floor(s / 60); if (m < 60) return `${m}m ago`; const h = Math.floor(m / 60); if (h < 24) return `${h}h ago`; const d = Math.floor(h / 24); return `${d}d ago`; }

const SocialFeed: React.FC = () => {
  const [posts, setPosts] = useState<Post[]>(() => {
    try { const saved = localStorage.getItem(STORAGE_POSTS); if (saved) { const parsed = JSON.parse(saved); return parsed.length > 0 ? parsed : DEMO_POSTS; } } catch { } return DEMO_POSTS;
  });
  const [following, setFollowing] = useState<string[]>(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_FOLLOWING) || '["friend_1","friend_2","friend_3","friend_4","friend_5"]'); } catch { return ['friend_1', 'friend_2', 'friend_3', 'friend_4', 'friend_5']; }
  });
  const [likedPosts, setLikedPosts] = useState<Record<string, boolean>>(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_LIKES) || '{}'); } catch { return {}; }
  });
  const [newPostText, setNewPostText] = useState('');
  const [showNewPost, setShowNewPost] = useState(false);
  const [commentInputs, setCommentInputs] = useState<Record<string, string>>({});
  const [expandedComments, setExpandedComments] = useState<Record<string, boolean>>({});
  const [showFriends, setShowFriends] = useState(false);

  const profile = (() => { try { return JSON.parse(localStorage.getItem('smarty_profile') || '{}'); } catch { return {}; } })();
  const userName = profile.name || 'You';
  const userInitials = userName.split(' ').map((s: string) => s[0]).join('').slice(0, 2).toUpperCase() || 'YO';

  useEffect(() => { localStorage.setItem(STORAGE_POSTS, JSON.stringify(posts)); }, [posts]);
  useEffect(() => { localStorage.setItem(STORAGE_FOLLOWING, JSON.stringify(following)); }, [following]);
  useEffect(() => { localStorage.setItem(STORAGE_LIKES, JSON.stringify(likedPosts)); }, [likedPosts]);

  const handlePost = () => {
    if (!newPostText.trim()) return;
    const post: Post = { id: generateId(), userId: 'self', userName, userAvatar: userInitials, text: newPostText.trim(), type: 'status', timestamp: new Date().toISOString(), comments: [] };
    setPosts(prev => [post, ...prev]);
    setNewPostText('');
    setShowNewPost(false);
  };

  const shareWorkout = () => {
    const logs: any[] = JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]');
    if (logs.length === 0) return;
    const latest = logs[0];
    const post: Post = { id: generateId(), userId: 'self', userName, userAvatar: userInitials, text: `Completed ${latest.template || latest.name || 'a workout'} — ${latest.duration || 0} min, ${latest.caloriesBurned || 0} calories burned!`, type: 'workout', workoutData: { type: latest.template || latest.name || 'Workout', duration: latest.duration || 0, calories: latest.caloriesBurned || 0 }, timestamp: new Date().toISOString(), comments: [] };
    setPosts(prev => [post, ...prev]);
  };

  const shareAchievement = () => {
    const earned: string[] = JSON.parse(localStorage.getItem('smarty_earned_achievements') || '[]');
    if (earned.length === 0) return;
    const last = earned[earned.length - 1];
    const post: Post = { id: generateId(), userId: 'self', userName, userAvatar: userInitials, text: `Just unlocked: ${last}! 🏆`, type: 'achievement', achievementData: { name: last, icon: '🏆' }, timestamp: new Date().toISOString(), comments: [] };
    setPosts(prev => [post, ...prev]);
  };

  const toggleLike = (postId: string) => {
    setLikedPosts(prev => ({ ...prev, [postId]: !prev[postId] }));
  };

  const handleComment = (postId: string) => {
    const text = commentInputs[postId]?.trim();
    if (!text) return;
    setPosts(prev => prev.map(p => p.id === postId ? { ...p, comments: [...p.comments, { id: generateId(), userId: 'self', userName, text, timestamp: new Date().toISOString() }] } : p));
    setCommentInputs(prev => ({ ...prev, [postId]: '' }));
  };

  const toggleFollow = (friendId: string) => {
    setFollowing(prev => prev.includes(friendId) ? prev.filter(f => f !== friendId) : [...prev, friendId]);
  };

  const visiblePosts = posts.filter(p => p.userId === 'self' || following.includes(p.userId));
  const hasWorkouts = (JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]')).length > 0;
  const hasAchievements = (JSON.parse(localStorage.getItem('smarty_earned_achievements') || '[]')).length > 0;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 bg-rose-500/10 border border-rose-500/20 rounded-3xl flex items-center justify-center text-rose-400">
            <Heart size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Social Feed</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Community activity & updates</p>
          </div>
        </div>
        <button onClick={() => setShowFriends(!showFriends)}
          className="flex items-center space-x-2 px-5 py-3 bg-white/5 border border-white/10 text-white hover:bg-white/10 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
          <User size={14} />
          <span>Friends ({following.length})</span>
        </button>
      </div>

      {/* Friends panel */}
      {showFriends && (
        <div className="glass-panel rounded-[2.5rem] border border-white/5 overflow-hidden">
          <div className="p-5 border-b border-white/5">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Friends & Following</p>
          </div>
          <div className="divide-y divide-white/5">
            {FRIENDS.map(f => {
              const isFollowing = following.includes(f.id);
              return (
                <div key={f.id} className="flex items-center justify-between p-4 hover:bg-white/[0.02] transition-colors">
                  <div className="flex items-center space-x-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-xs font-black ${f.color}`}>{f.avatar}</div>
                    <div>
                      <p className="text-sm font-black text-white">{f.name}</p>
                      <p className="text-[8px] text-slate-600 font-black uppercase tracking-widest mt-0.5">{f.bio}</p>
                    </div>
                  </div>
                  <button onClick={() => toggleFollow(f.id)}
                    className={`px-4 py-2 rounded-xl text-[8px] font-black uppercase tracking-widest transition-all border ${
                      isFollowing ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400' : 'bg-slate-900 border-slate-800 text-slate-500 hover:text-white'
                    }`}>
                    {isFollowing ? 'Following' : 'Follow'}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Create post */}
      <div className="glass-panel rounded-[2.5rem] border border-white/5 p-5">
        {showNewPost ? (
          <div className="space-y-4">
            <textarea value={newPostText} onChange={e => setNewPostText(e.target.value)}
              placeholder="Share your fitness journey..."
              className="w-full bg-slate-950 border border-white/10 rounded-2xl px-5 py-4 text-xs text-white placeholder:text-slate-600 resize-none h-24" autoFocus />
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <button onClick={shareWorkout} disabled={!hasWorkouts}
                  className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-white/[0.03] border border-white/5 text-slate-500 hover:text-emerald-400 text-[8px] font-black uppercase tracking-widest transition disabled:opacity-30">
                  <Dumbbell size={12} /> <span>Workout</span>
                </button>
                <button onClick={shareAchievement} disabled={!hasAchievements}
                  className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-white/[0.03] border border-white/5 text-slate-500 hover:text-amber-400 text-[8px] font-black uppercase tracking-widest transition disabled:opacity-30">
                  <Trophy size={12} /> <span>Achievement</span>
                </button>
              </div>
              <div className="flex items-center space-x-3">
                <button onClick={() => { setShowNewPost(false); setNewPostText(''); }}
                  className="text-[9px] text-slate-600 font-black uppercase tracking-widest hover:text-slate-400 transition">Cancel</button>
                <button onClick={handlePost} disabled={!newPostText.trim()}
                  className="px-5 py-2.5 bg-rose-500 hover:bg-rose-400 text-slate-950 rounded-xl font-black text-[9px] uppercase tracking-widest transition disabled:opacity-50 flex items-center space-x-1.5">
                  <Send size={12} /> <span>Post</span>
                </button>
              </div>
            </div>
          </div>
        ) : (
          <button onClick={() => setShowNewPost(true)}
            className="w-full flex items-center space-x-4">
            <div className="w-10 h-10 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 text-xs font-black shrink-0">
              {userInitials}
            </div>
            <span className="text-xs text-slate-600 font-medium">Share your fitness update...</span>
            <div className="flex items-center space-x-2 ml-auto">
              <button onClick={(e) => { e.stopPropagation(); shareWorkout(); }}
                className="p-2 rounded-xl hover:bg-white/5 text-slate-600 hover:text-emerald-400 transition" title="Share latest workout">
                <Dumbbell size={14} />
              </button>
              <button onClick={(e) => { e.stopPropagation(); shareAchievement(); }}
                className="p-2 rounded-xl hover:bg-white/5 text-slate-600 hover:text-amber-400 transition" title="Share latest achievement">
                <Trophy size={14} />
              </button>
              <Plus size={16} className="text-slate-500" />
            </div>
          </button>
        )}
      </div>

      {/* Feed */}
      <div className="space-y-4">
        {visiblePosts.map(post => {
          const likeCount = likedPosts[post.id] ? 1 : 0;
          const isLiked = likedPosts[post.id];
          const friend = FRIENDS.find(f => f.id === post.userId);
          const isSelf = post.userId === 'self';
          const showComments = expandedComments[post.id];

          return (
            <div key={post.id} className="glass-panel rounded-[2.5rem] border border-white/5 overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center space-x-4">
                  <div className={`w-11 h-11 rounded-full flex items-center justify-center text-xs font-black ${
                    isSelf ? 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-400' : (friend?.color || 'bg-slate-900 border border-slate-800 text-slate-500')
                  }`}>
                    {post.userAvatar}
                  </div>
                  <div>
                    <p className="text-sm font-black text-white">{post.userName}</p>
                    <div className="flex items-center space-x-2 mt-0.5">
                      <span className="text-[8px] text-slate-600 font-black uppercase tracking-widest">{timeAgo(post.timestamp)}</span>
                      {post.type === 'workout' && <span className="text-[8px] text-emerald-500 font-black">🏋️ Workout</span>}
                      {post.type === 'achievement' && <span className="text-[8px] text-amber-500 font-black">🏆 Achievement</span>}
                      {post.type === 'progress' && <span className="text-[8px] text-blue-500 font-black">📈 Progress</span>}
                    </div>
                  </div>
                </div>
                {!isSelf && (
                  <button onClick={() => toggleFollow(post.userId)}
                    className={`text-[8px] font-black uppercase tracking-widest transition ${
                      following.includes(post.userId) ? 'text-emerald-500 hover:text-emerald-400' : 'text-slate-600 hover:text-white'
                    }`}>
                    {following.includes(post.userId) ? '✓ Following' : '+ Follow'}
                  </button>
                )}
              </div>

              {/* Content */}
              <div className="px-5 pb-3">
                <p className="text-xs text-slate-300 leading-relaxed">{post.text}</p>
              </div>

              {/* Workout card */}
              {post.workoutData && (
                <div className="mx-5 mb-4 p-4 rounded-2xl bg-gradient-to-br from-emerald-500/5 to-emerald-500/10 border border-emerald-500/20">
                  <div className="flex items-center space-x-2 mb-3">
                    <Zap size={14} className="text-emerald-400" />
                    <span className="text-[9px] text-emerald-400 font-black uppercase tracking-widest">{post.workoutData.type}</span>
                  </div>
                  <div className="flex space-x-6">
                    <div><span className="text-lg font-black text-white">{post.workoutData.duration}</span><span className="text-[8px] text-slate-500 ml-1">min</span></div>
                    <div><span className="text-lg font-black text-amber-400">{post.workoutData.calories}</span><span className="text-[8px] text-slate-500 ml-1">kcal</span></div>
                    {post.workoutData.distance && <div><span className="text-lg font-black text-blue-400">{post.workoutData.distance}</span></div>}
                    {post.workoutData.exercise && <div><span className="text-[9px] text-slate-400 font-black">{post.workoutData.exercise}</span></div>}
                  </div>
                </div>
              )}

              {/* Achievement card */}
              {post.achievementData && (
                <div className="mx-5 mb-4 p-4 rounded-2xl bg-gradient-to-br from-amber-500/5 to-amber-500/10 border border-amber-500/20">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{post.achievementData.icon || '🏆'}</span>
                    <div>
                      <p className="text-[9px] text-amber-400 font-black uppercase tracking-widest">Achievement Unlocked</p>
                      <p className="text-sm font-black text-white mt-0.5">{post.achievementData.name}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center justify-between px-5 py-3 border-t border-white/5">
                <div className="flex items-center space-x-6">
                  <button onClick={() => toggleLike(post.id)}
                    className={`flex items-center space-x-1.5 text-[9px] font-black uppercase tracking-widest transition ${
                      isLiked ? 'text-rose-400' : 'text-slate-600 hover:text-rose-400'
                    }`}>
                    <Heart size={14} className={isLiked ? 'fill-rose-400' : ''} />
                    <span>Like{likeCount > 0 ? ` (${likeCount})` : ''}</span>
                  </button>
                  <button onClick={() => setExpandedComments(prev => ({ ...prev, [post.id]: !prev[post.id] }))}
                    className="flex items-center space-x-1.5 text-[9px] text-slate-600 font-black uppercase tracking-widest hover:text-white transition">
                    <MessageCircle size={14} />
                    <span>{post.comments.length > 0 ? `(${post.comments.length})` : ''} Comment</span>
                  </button>
                  <button className="flex items-center space-x-1.5 text-[9px] text-slate-600 font-black uppercase tracking-widest hover:text-white transition">
                    <Share2 size={14} />
                    <span>Share</span>
                  </button>
                </div>
              </div>

              {/* Comments */}
              {showComments && (
                <div className="border-t border-white/5">
                  {post.comments.map(c => (
                    <div key={c.id} className="flex items-start space-x-3 px-5 py-3 bg-white/[0.01]">
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[7px] font-black shrink-0 ${
                        c.userId === 'self' ? 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-400' : 'bg-slate-900 border border-slate-800 text-slate-500'
                      }`}>{c.userName.slice(0, 2).toUpperCase()}</div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[10px] font-black text-white">{c.userName} <span className="text-[7px] text-slate-600 font-normal ml-2">{timeAgo(c.timestamp)}</span></p>
                        <p className="text-[10px] text-slate-400 mt-0.5">{c.text}</p>
                      </div>
                    </div>
                  ))}
                  <div className="flex items-center space-x-3 px-5 py-3 border-t border-white/5">
                    <div className="w-7 h-7 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 text-[7px] font-black shrink-0">{userInitials}</div>
                    <input value={commentInputs[post.id] || ''} onChange={e => setCommentInputs(prev => ({ ...prev, [post.id]: e.target.value }))}
                      onKeyDown={e => e.key === 'Enter' && handleComment(post.id)}
                      placeholder="Write a comment..."
                      className="flex-1 bg-transparent border-none text-[10px] text-white placeholder:text-slate-600 outline-none" />
                    <button onClick={() => handleComment(post.id)} disabled={!commentInputs[post.id]?.trim()}
                      className="p-1.5 rounded-lg text-rose-400 disabled:text-slate-700 transition">
                      <Send size={14} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SocialFeed;
