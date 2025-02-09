from fastapi import Request, Depends,HTTPException
import time

rate_limit_cache = {}

def rate_limiter(request: Request):
    client_ip = request.client.host
    current_time = time.time()

    if client_ip in rate_limit_cache:
        last_request_time = rate_limit_cache[client_ip]
        if current_time - last_request_time < 10:  
            raise HTTPException(status_code=429, detail="Too many requests. Slow down!")

    rate_limit_cache[client_ip] = current_time
