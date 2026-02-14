
from fastapi import HTTPException, Header

# In a real app, this would check JWTs or DB tokens
def validate_operator_link(operator_id: str = Header(None)):
    """Simple check to ensure the request is from an authorized operator."""
    if not operator_id:
        # Fallback to demo user if no header provided
        return "user-1"
    
    # Example logic: block guest access if we wanted
    if operator_id == "GUEST":
        raise HTTPException(status_code=403, detail="Guest access to Neural Core denied.")
        
    return operator_id
