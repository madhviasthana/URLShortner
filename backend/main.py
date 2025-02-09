from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import Column, Integer, String, create_engine, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import random
import string
import qrcode
from io import BytesIO
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, Request, Body
from pydantic import BaseModel
from typing import Optional
# Database setup
DATABASE_URL = "sqlite:///./url_shortener.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ClickAnalytics(Base):
    __tablename__ = "click_analytics"
    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)
    user_agent = Column(String)

class URL(Base):
    __tablename__ = "urls"
    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True)
    original_url = Column(String)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to generate a short code
def generate_short_code(length=7):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))



# Add a Pydantic model to validate the request body
class ShortenRequest(BaseModel):
    original_url: str
    custom_code: Optional[str] = None

@app.post("/shorten")
def create_short_url(request: Request, shorten_request: ShortenRequest = Body(...), db: Session = Depends(get_db)):
    print(f"Received request: original_url={shorten_request.original_url}, custom_code={shorten_request.custom_code}")  # Debugging

    # Check if a custom code is provided
    if shorten_request.custom_code:
        if db.query(URL).filter(URL.short_code == shorten_request.custom_code).first():
            raise HTTPException(status_code=400, detail="Custom short code already exists!")
        short_code = shorten_request.custom_code
    else:
        # Ensure unique short code
        short_code = generate_short_code()
        while db.query(URL).filter(URL.short_code == short_code).first():
            short_code = generate_short_code()

    # Save URL to the database
    new_url = URL(short_code=short_code, original_url=shorten_request.original_url)
    db.add(new_url)
    db.commit()
    db.refresh(new_url)  # Ensure it's saved

    print(f"✅ Short URL Created: {request.base_url}{short_code}")  # Debugging
    return {"short_url": f"{request.base_url}{short_code}", "original_url": shorten_request.original_url}

# Route to redirect to the original URL
@app.get("/{short_code}")
def redirect_to_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    print(f"🔍 Searching for Short Code: {short_code}")  # Debugging

    # Fetch the URL entry
    url_entry = db.query(URL).filter(URL.short_code == short_code).first()

    if not url_entry:
        print(f"❌ Short URL '{short_code}' NOT FOUND in database!")  # Debugging
        raise HTTPException(status_code=404, detail="Short URL not found")

    print(f"✅ Found URL: {url_entry.original_url}, Redirecting...")  # Debugging

    # ✅ Fix: Ensure Click Analytics is stored in the database
    try:
        click = ClickAnalytics(
            short_code=short_code,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
        db.add(click)
        db.commit()  # ✅ Ensure it's saved
        db.refresh(click)  # ✅ Ensure the record is updated
        print(f"📊 Click analytics saved for {short_code}")  # Debugging
    except Exception as e:
        print(f"⚠️ Failed to save analytics: {e}")  # Debugging

    return RedirectResponse(url_entry.original_url, status_code=302)


# Route to generate a QR code for a short URL
@app.get("/qr/{short_code}")
def generate_qr_code(short_code: str, db: Session = Depends(get_db)):
    print(f"🔍 Received short_code: {short_code}")  # Debugging

    url_entry = db.query(URL).filter(URL.short_code == short_code).first()

    if not url_entry:
        raise HTTPException(status_code=404, detail=f"Short URL '{short_code}' not found in the database")

    # Generate QR Code
    qr = qrcode.make(url_entry.original_url)
    img_io = BytesIO()
    qr.save(img_io, format="PNG")
    img_io.seek(0)
    return StreamingResponse(img_io, media_type="image/png")

# Debug Route: Get All URLs Stored in DB
@app.get("/debug/urls")
def get_all_urls(db: Session = Depends(get_db)):
    urls = db.query(URL).all()
    return [{"short_code": url.short_code, "original_url": url.original_url} for url in urls]

@app.get("/analytics")
def get_click_analytics(short_code: str = None, db: Session = Depends(get_db)):
    """
    Get analytics for a specific short URL or all stored analytics.
    """
    if short_code:
        analytics = db.query(ClickAnalytics).filter(ClickAnalytics.short_code == short_code).all()
        if not analytics:
            raise HTTPException(status_code=404, detail=f"No analytics data found for '{short_code}'")
    else:
        analytics = db.query(ClickAnalytics).all()
        if not analytics:
            raise HTTPException(status_code=404, detail="No analytics data found")

    return [
        {
            "short_code": click.short_code,
            "timestamp": click.timestamp,
            "ip_address": click.ip_address,
            "user_agent": click.user_agent
        }
        for click in analytics
    ]

from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File
import csv
import io
from fastapi.responses import StreamingResponse

@app.post("/bulk_shorten")
async def bulk_shorten(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Endpoint to accept CSV file, shorten all URLs, and return a downloadable CSV.
    """
    try:
        contents = await file.read()
        file_stream = io.StringIO(contents.decode("utf-8"))
        csv_reader = csv.reader(file_stream)

        output = io.StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerow(["Original URL", "Shortened URL"])

        for row in csv_reader:
            if not row:
                continue
            original_url = row[0]

            # Generate a unique short code
            short_code = generate_short_code()
            while db.query(URL).filter(URL.short_code == short_code).first():
                short_code = generate_short_code()

            new_url = URL(short_code=short_code, original_url=original_url)
            db.add(new_url)
            db.commit()

            short_url = f"https://urlshort.themadhvi.com/{short_code}"
            csv_writer.writerow([original_url, short_url])

        output.seek(0)
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=shortened_urls.csv"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image
import io

@app.post("/convert_pdf")
async def convert_images_to_pdf(images: list[UploadFile] = File(...)):
    """
    Convert multiple uploaded images into a single PDF file.
    """
    image_list = []
    
    try:
        for image_file in images:
            image = Image.open(io.BytesIO(await image_file.read()))
            if image.mode != 'RGB':
                image = image.convert('RGB')  # Convert to RGB if necessary
            image_list.append(image)
        
        if not image_list:
            raise HTTPException(status_code=400, detail="No valid images provided")

        # Convert images to a PDF
        pdf_bytes = io.BytesIO()
        image_list[0].save(pdf_bytes, format="PDF", save_all=True, append_images=image_list[1:])
        pdf_bytes.seek(0)

        return StreamingResponse(pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=converted.pdf"})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing images: {str(e)}")

