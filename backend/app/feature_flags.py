import hashlib

def is_feature_enabled_for_user(user_id: str, flag_name: str, rollout_percentage: int) -> bool:
    """
    Stateless hash-based percentage feature flag rollout.
    Deterministically evaluates if a user falls within the rollout percentage (0-100).
    """
    if rollout_percentage >= 100:
        return True
    if rollout_percentage <= 0:
        return False
        
    # Salt the hash with the feature flag name to avoid skewing same users on every flag
    key = f"{flag_name}:{user_id}".encode("utf-8")
    hasher = hashlib.sha256(key)
    hex_digest = hasher.hexdigest()
    
    # Take first 8 chars, convert to integer, modulo 100
    hash_int = int(hex_digest[:8], 16)
    bucket = hash_int % 100
    
    return bucket < rollout_percentage
