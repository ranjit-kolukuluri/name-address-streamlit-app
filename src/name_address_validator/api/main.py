# src/name_address_validator/api/main.py
"""
Name Validation REST API Server
FastAPI-based REST API for name validation services
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd
import json
import uuid
import time
import os
from datetime import datetime
from pathlib import Path
import sys
import tempfile
import asyncio

# Setup paths
current_file = Path(__file__).resolve()
src_dir = current_file.parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import validation service
try:
    from name_address_validator.services.validation_service import ValidationService
    from name_address_validator.utils.logger import AppLogger
    VALIDATION_AVAILABLE = True
except ImportError as e:
    print(f"❌ Import Error: {e}")
    VALIDATION_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(
    title="Name Validation API",
    description="Professional name validation service with dictionary-based validation",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
validation_service = None
logger = None
processing_jobs = {}  # Store background processing jobs

# Pydantic models for API requests/responses
class NameRecord(BaseModel):
    uniqueid: str = Field(..., description="Unique identifier for the record")
    name: str = Field(..., description="Full name to validate")
    gender: Optional[str] = Field("", description="Optional gender hint (M/F)")
    party_type: Optional[str] = Field("", description="Optional party type (I/O)")
    parseInd: Optional[str] = Field("", description="Parse indicator (Y/N)")

class NameValidationRequest(BaseModel):
    records: List[NameRecord] = Field(..., description="List of name records to validate")
    
    class Config:
        schema_extra = {
            "example": {
                "records": [
                    {
                        "uniqueid": "001",
                        "name": "John Michael Smith",
                        "gender": "",
                        "party_type": "I",
                        "parseInd": "Y"
                    },
                    {
                        "uniqueid": "002",
                        "name": "TechCorp Solutions LLC",
                        "gender": "",
                        "party_type": "O",
                        "parseInd": "N"
                    }
                ]
            }
        }

class ParsedComponents(BaseModel):
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    middle_name: Optional[str] = ""
    organization_name: Optional[str] = ""

class Suggestions(BaseModel):
    name_suggestions: Optional[List[str]] = []
    gender_prediction: Optional[str] = ""
    party_type_prediction: Optional[str] = ""

class ValidationResult(BaseModel):
    uniqueid: str
    name: str
    gender: str
    party_type: str
    parse_indicator: str
    validation_status: str
    confidence_score: float
    parsed_components: ParsedComponents
    suggestions: Suggestions
    errors: List[str]
    warnings: List[str]

class NameValidationResponse(BaseModel):
    status: str
    processed_count: int
    successful_count: int
    results: List[ValidationResult]
    processing_time_ms: int
    timestamp: str

class CSVProcessingRequest(BaseModel):
    csv_url: Optional[str] = Field(None, description="URL to CSV file")
    csv_path: Optional[str] = Field(None, description="Local file path to CSV")
    max_records: Optional[int] = Field(1000, description="Maximum records to process")
    include_suggestions: Optional[bool] = Field(True, description="Include suggestions in response")
    
    class Config:
        schema_extra = {
            "example": {
                "csv_url": "https://example.com/names.csv",
                "max_records": 500,
                "include_suggestions": True
            }
        }

class JobStatus(BaseModel):
    job_id: str
    status: str  # "processing", "completed", "failed"
    progress: float  # 0.0 to 1.0
    processed_count: int
    total_count: int
    start_time: str
    estimated_completion: Optional[str] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None

class APIError(BaseModel):
    error: str
    detail: str
    timestamp: str

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize validation service on startup"""
    global validation_service, logger
    
    print("🚀 Starting Name Validation API Server...")
    
    if not VALIDATION_AVAILABLE:
        print("❌ Validation service not available - check imports")
        return
    
    try:
        logger = AppLogger()
        validation_service = ValidationService(debug_callback=logger.log)
        
        if validation_service.is_name_validation_available():
            print("✅ Name validation service initialized successfully")
        else:
            print("⚠️ Name validation service available but dictionaries may be missing")
            
        logger.log("API server started successfully", "API_SERVER")
        
    except Exception as e:
        print(f"❌ Failed to initialize validation service: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "validation_available": validation_service is not None and validation_service.is_name_validation_available(),
        "version": "2.0.0"
    }

# Service status endpoint
@app.get("/status")
async def service_status():
    """Get detailed service status"""
    if not validation_service:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Service unavailable",
                "detail": "Validation service not initialized",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    return {
        "service_status": {
            "name_validation_available": validation_service.is_name_validation_available(),
            "address_validation_available": validation_service.is_address_validation_available(),
            "dictionary_support": hasattr(validation_service, 'name_standardizer'),
            "api_version": "2.0.0",
            "server_time": datetime.now().isoformat()
        }
    }

# Single name validation endpoint
@app.post("/api/v1/validate-names", response_model=NameValidationResponse)
async def validate_names(request: NameValidationRequest):
    """
    Validate a list of names and return structured results
    
    - **records**: List of name records to validate
    - **uniqueid**: Unique identifier for each record
    - **name**: Full name to validate
    - **gender**: Optional gender hint (M/F)
    - **party_type**: Optional party type hint (I=Individual, O=Organization)  
    - **parseInd**: Parse indicator (Y=parse name, N=use as-is, empty=auto-detect)
    """
    
    if not validation_service:
        raise HTTPException(
            status_code=503,
            detail="Validation service not available"
        )
    
    if not validation_service.is_name_validation_available():
        raise HTTPException(
            status_code=503,
            detail="Name validation service not configured"
        )
    
    start_time = time.time()
    
    try:
        # Convert Pydantic models to dict format expected by validation service
        records_dict = [record.dict() for record in request.records]
        
        # Process validation
        results = []
        successful_count = 0
        
        for record in records_dict:
            try:
                # Use the existing validation logic
                result = await process_single_name_record(record)
                results.append(result)
                
                if result['validation_status'] != 'error':
                    successful_count += 1
                    
            except Exception as e:
                error_result = create_error_result(record, str(e))
                results.append(error_result)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response = NameValidationResponse(
            status="success",
            processed_count=len(results),
            successful_count=successful_count,
            results=[ValidationResult(**result) for result in results],
            processing_time_ms=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
        # Log the API call
        logger.log(f"API call processed: {len(request.records)} records, {successful_count} successful", "API_CALL")
        
        return response
        
    except Exception as e:
        logger.log(f"API validation error: {e}", "API_ERROR", level="ERROR")
        raise HTTPException(
            status_code=500,
            detail=f"Validation processing failed: {str(e)}"
        )

# CSV file upload endpoint
@app.post("/api/v1/validate-csv-upload")
async def validate_csv_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    max_records: int = 1000,
    include_suggestions: bool = True
):
    """
    Upload CSV file for name validation processing
    
    - **file**: CSV file to upload and process
    - **max_records**: Maximum number of records to process
    - **include_suggestions**: Include validation suggestions
    """
    
    if not validation_service:
        raise HTTPException(status_code=503, detail="Validation service not available")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file temporarily
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"{job_id}_{file.filename}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Initialize job status
        processing_jobs[job_id] = JobStatus(
            job_id=job_id,
            status="processing",
            progress=0.0,
            processed_count=0,
            total_count=0,
            start_time=datetime.now().isoformat()
        )
        
        # Add background task
        background_tasks.add_task(
            process_csv_file_background,
            job_id, temp_file_path, max_records, include_suggestions
        )
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "CSV file uploaded and processing started",
            "check_status_url": f"/api/v1/job/{job_id}/status",
            "estimated_time": f"~{max_records // 100} minutes"
        }
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"File upload processing failed: {str(e)}"
        )

# CSV URL processing endpoint
@app.post("/api/v1/validate-csv-url")
async def validate_csv_url(
    background_tasks: BackgroundTasks,
    request: CSVProcessingRequest
):
    """
    Process CSV file from URL or local path
    
    - **csv_url**: URL to CSV file to download and process
    - **csv_path**: Local file system path to CSV file
    - **max_records**: Maximum records to process
    - **include_suggestions**: Include suggestions in response
    """
    
    if not validation_service:
        raise HTTPException(status_code=503, detail="Validation service not available")
    
    if not request.csv_url and not request.csv_path:
        raise HTTPException(status_code=400, detail="Either csv_url or csv_path must be provided")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    processing_jobs[job_id] = JobStatus(
        job_id=job_id,
        status="processing",
        progress=0.0,
        processed_count=0,
        total_count=0,
        start_time=datetime.now().isoformat()
    )
    
    # Add background task
    background_tasks.add_task(
        process_csv_url_background,
        job_id, request.csv_url, request.csv_path, 
        request.max_records, request.include_suggestions
    )
    
    return {
        "job_id": job_id,
        "status": "processing", 
        "message": "CSV processing started",
        "check_status_url": f"/api/v1/job/{job_id}/status",
        "estimated_time": f"~{request.max_records // 100} minutes"
    }

# Job status endpoint
@app.get("/api/v1/job/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of a background processing job"""
    
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return processing_jobs[job_id]

# Download results endpoint
@app.get("/api/v1/job/{job_id}/download")
async def download_job_results(job_id: str):
    """Download the results of a completed job"""
    
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    if not job.download_url or not os.path.exists(job.download_url):
        raise HTTPException(status_code=404, detail="Results file not found")
    
    return FileResponse(
        job.download_url,
        media_type='application/json',
        filename=f"validation_results_{job_id}.json"
    )

# Helper functions
async def process_single_name_record(record: Dict) -> Dict:
    """Process a single name record"""
    
    uniqueid = record['uniqueid']
    name = record['name'].strip()
    gender_hint = record.get('gender', '').strip()
    party_type_hint = record.get('party_type', '').strip()
    parse_ind = record.get('parseInd', '').strip()
    
    # Initialize result
    result = {
        'uniqueid': uniqueid,
        'name': name,
        'gender': gender_hint,
        'party_type': party_type_hint,
        'parse_indicator': parse_ind,
        'validation_status': 'valid',
        'confidence_score': 0.0,
        'parsed_components': ParsedComponents().dict(),
        'suggestions': Suggestions().dict(),
        'errors': [],
        'warnings': []
    }
    
    # Determine if organization
    is_org = detect_organization(name, party_type_hint)
    
    if is_org:
        # Handle organization
        result['party_type'] = 'O'
        result['gender'] = ''
        result['parse_indicator'] = 'N'
        result['parsed_components'] = ParsedComponents(
            organization_name=name,
            first_name='',
            last_name='',
            middle_name=''
        ).dict()
        result['confidence_score'] = 0.9
        
    else:
        # Handle individual name
        result['party_type'] = 'I'
        
        # Parse name if requested
        if parse_ind.upper() == 'Y' or parse_ind == '':
            parsed = parse_individual_name(name)
            result['parsed_components'] = parsed
            result['parse_indicator'] = 'Y'
            
            # Validate using existing service if available
            first_name = parsed.get('first_name', '')
            last_name = parsed.get('last_name', '')
            
            if first_name or last_name:
                if validation_service.name_validator:
                    # Use existing validator
                    validation_result = validation_service.name_validator.validate(first_name, last_name)
                    result['validation_status'] = 'valid' if validation_result.get('valid') else 'warning'
                    result['confidence_score'] = validation_result.get('confidence', 0.8)
                else:
                    result['validation_status'] = 'valid'
                    result['confidence_score'] = 0.7
                
                # Predict gender
                if not gender_hint and first_name:
                    predicted_gender = predict_gender(first_name)
                    if predicted_gender:
                        result['gender'] = predicted_gender
                        result['suggestions']['gender_prediction'] = predicted_gender
            else:
                result['validation_status'] = 'invalid'
                result['errors'].append('Could not parse name into valid components')
                result['confidence_score'] = 0.2
        else:
            result['parse_indicator'] = 'N'
            result['parsed_components'] = ParsedComponents(
                first_name='',
                last_name='',
                middle_name=''
            ).dict()
            result['confidence_score'] = 0.6
    
    # Add party type prediction if not provided
    if not party_type_hint:
        result['suggestions']['party_type_prediction'] = result['party_type']
    
    return result

def create_error_result(record: Dict, error_message: str) -> Dict:
    """Create error result for failed processing"""
    return {
        'uniqueid': record.get('uniqueid', ''),
        'name': record.get('name', ''),
        'gender': '',
        'party_type': '',
        'parse_indicator': '',
        'validation_status': 'error',
        'confidence_score': 0.0,
        'parsed_components': ParsedComponents().dict(),
        'suggestions': Suggestions().dict(),
        'errors': [error_message],
        'warnings': []
    }

def detect_organization(name: str, party_type_hint: str) -> bool:
    """Detect if name is an organization"""
    if party_type_hint.upper() == 'O':
        return True
    elif party_type_hint.upper() == 'I':
        return False
    
    # Auto-detect based on name
    name_lower = name.lower()
    org_indicators = [
        'llc', 'inc', 'corp', 'company', 'ltd', 'co.', 'corporation',
        'hospital', 'medical', 'clinic', 'center', 'services', 'solutions',
        'group', 'partners', 'associates', 'firm', 'office', 'bank',
        'trust', 'foundation', 'institute', 'university', 'college'
    ]
    
    return any(indicator in name_lower for indicator in org_indicators)

def parse_individual_name(full_name: str) -> Dict[str, str]:
    """Parse individual name into components"""
    if not full_name or not full_name.strip():
        return ParsedComponents().dict()
    
    # Simple parsing logic
    parts = full_name.strip().split()
    
    if len(parts) == 0:
        return ParsedComponents().dict()
    elif len(parts) == 1:
        return ParsedComponents(first_name=parts[0]).dict()
    elif len(parts) == 2:
        return ParsedComponents(first_name=parts[0], last_name=parts[1]).dict()
    else:
        return ParsedComponents(
            first_name=parts[0],
            last_name=parts[-1],
            middle_name=' '.join(parts[1:-1])
        ).dict()

def predict_gender(first_name: str) -> str:
    """Predict gender from first name"""
    if not first_name:
        return ''
    
    # Use validation service if available
    if (validation_service and 
        hasattr(validation_service, 'name_standardizer') and
        validation_service.name_standardizer and
        hasattr(validation_service.name_standardizer, 'dictionary_loader')):
        
        return validation_service.name_standardizer.dictionary_loader.predict_gender(first_name)
    
    # Simple heuristic fallback
    name_lower = first_name.lower()
    if name_lower.endswith(('a', 'ia', 'ella')):
        return 'F'
    elif name_lower.endswith(('er', 'on', 'an')):
        return 'M'
    
    return ''

# Background processing functions
async def process_csv_file_background(job_id: str, file_path: str, max_records: int, include_suggestions: bool):
    """Background task to process CSV file"""
    
    try:
        # Update job status
        processing_jobs[job_id].status = "processing"
        processing_jobs[job_id].progress = 0.1
        
        # Read CSV file
        df = pd.read_csv(file_path)
        total_count = min(len(df), max_records)
        processing_jobs[job_id].total_count = total_count
        
        # Process records
        results = []
        for i, row in df.head(max_records).iterrows():
            # Create record from CSV row
            record = extract_record_from_csv_row(row, i)
            
            # Process validation
            result = await process_single_name_record(record)
            results.append(result)
            
            # Update progress
            processing_jobs[job_id].processed_count = len(results)
            processing_jobs[job_id].progress = len(results) / total_count
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.01)
        
        # Save results to file
        results_file = save_results_to_file(job_id, results)
        
        # Update job completion
        processing_jobs[job_id].status = "completed"
        processing_jobs[job_id].progress = 1.0
        processing_jobs[job_id].download_url = results_file
        
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        processing_jobs[job_id].status = "failed"
        processing_jobs[job_id].error_message = str(e)
        logger.log(f"Background CSV processing failed: {e}", "BACKGROUND_TASK", level="ERROR")

async def process_csv_url_background(job_id: str, csv_url: Optional[str], csv_path: Optional[str], max_records: int, include_suggestions: bool):
    """Background task to process CSV from URL or path"""
    
    try:
        # Update job status
        processing_jobs[job_id].status = "processing"
        processing_jobs[job_id].progress = 0.1
        
        # Load CSV data
        if csv_url:
            df = pd.read_csv(csv_url)
        elif csv_path:
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"CSV file not found: {csv_path}")
            df = pd.read_csv(csv_path)
        else:
            raise ValueError("No CSV source provided")
        
        total_count = min(len(df), max_records)
        processing_jobs[job_id].total_count = total_count
        
        # Process records (similar to file processing)
        results = []
        for i, row in df.head(max_records).iterrows():
            record = extract_record_from_csv_row(row, i)
            result = await process_single_name_record(record)
            results.append(result)
            
            processing_jobs[job_id].processed_count = len(results)
            processing_jobs[job_id].progress = len(results) / total_count
            
            await asyncio.sleep(0.01)
        
        # Save results
        results_file = save_results_to_file(job_id, results)
        
        processing_jobs[job_id].status = "completed"
        processing_jobs[job_id].progress = 1.0
        processing_jobs[job_id].download_url = results_file
        
    except Exception as e:
        processing_jobs[job_id].status = "failed"
        processing_jobs[job_id].error_message = str(e)
        logger.log(f"Background CSV URL processing failed: {e}", "BACKGROUND_TASK", level="ERROR")

def extract_record_from_csv_row(row: pd.Series, index: int) -> Dict:
    """Extract name record from CSV row - FIXED VERSION"""
    
    # Enhanced column mapping to handle different naming conventions
    column_mappings = {
        'uniqueid': ['uniqueid', 'uniqueId', 'unique_id', 'UniqueId', 'UNIQUEID', 'id', 'Id', 'ID'],
        'name': ['name', 'Name', 'NAME', 'full_name', 'fullname', 'FullName', 'Full_Name'],
        'gender': ['gender', 'Gender', 'GENDER', 'sex', 'Sex', 'SEX'],
        'party_type': ['party_type', 'partyType', 'PartyType', 'Party_Type', 'PARTY_TYPE', 'type', 'Type'],
        'parseInd': ['parseInd', 'parse_ind', 'ParseInd', 'Parse_Ind', 'PARSE_IND', 'parseind']
    }
    
    def find_column_value(field_mappings: List[str], default: str = '') -> str:
        """Find the first matching column and return its value"""
        for col_name in field_mappings:
            if col_name in row.index and pd.notna(row[col_name]):
                value = str(row[col_name]).strip()
                if value and value.lower() not in ['nan', 'none', '']:
                    return value
        return default
    
    # Extract values using the enhanced mapping
    uniqueid = find_column_value(column_mappings['uniqueid'], f'row_{index+1}')
    name = find_column_value(column_mappings['name'], '')
    gender = find_column_value(column_mappings['gender'], '')
    party_type = find_column_value(column_mappings['party_type'], '')
    parse_ind = find_column_value(column_mappings['parseInd'], 'Y')
    
    # Debug logging
    print(f"[CSV] Row {index+1}: uniqueid='{uniqueid}', name='{name}', gender='{gender}', party_type='{party_type}', parseInd='{parse_ind}'")
    
    return {
        'uniqueid': uniqueid,
        'name': name,
        'gender': gender,
        'party_type': party_type,
        'parseInd': parse_ind
    }

def save_results_to_file(job_id: str, results: List[Dict]) -> str:
    """Save results to JSON file and return file path"""
    
    temp_dir = tempfile.gettempdir()
    results_file = os.path.join(temp_dir, f"results_{job_id}.json")
    
    response_data = {
        'status': 'success',
        'processed_count': len(results),
        'successful_count': sum(1 for r in results if r['validation_status'] != 'error'),
        'results': results,
        'timestamp': datetime.now().isoformat(),
        'job_id': job_id
    }
    
    with open(results_file, 'w') as f:
        json.dump(response_data, f, indent=2)
    
    return results_file

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)