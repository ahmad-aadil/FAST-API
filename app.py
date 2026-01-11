from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, computed_field, Field
from typing import Annotated, Literal, Optional
import json

app = FastAPI()


class Patient(BaseModel):
    id: Annotated[str, Field(..., description="ID of the pateint", examples=["P001"])]
    name: Annotated[str, Field(..., description="Name of the pateint")]
    city: Annotated[str, Field(..., description="City of the pateint")]
    age: Annotated[int, Field(..., gt=0, lt=120, description="Age of the pateint")]
    gender: Annotated[
        Literal["male", "female", "other"],
        Field(..., description="Gender of the pateint"),
    ]
    height: Annotated[float, Field(..., gt=0, description="Height of patient in mtrs")]
    weight: Annotated[float, Field(..., gt=0, description="Weight of patient in kgs")]


class PatientUpdate(BaseModel):

    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[
        Optional[Literal["male", "female", "other"]],
        Field(default=None),
    ]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]


@computed_field
@property
def bmi(self) -> float:
    bmi = round(self.weight / (self.height**2), 2)
    return bmi


@computed_field
@property
def verdict(self) -> str:
    if self.bmi < 18.5:
        return "Underweight"
    elif self.bmi < 25:
        return "Normal"
    elif self.bmi < 30:
        return "Normal"
    else:
        return "Obese"


def load_data():
    with open("patients.json", "r") as f:
        data = json.load(f)
    return data


def save_data(data):
    with open("patients.json", "w") as f:
        json.dump(data, f)


@app.get("/")
def hello():
    return {"Message": "Hello from FAST API Endpoint"}


@app.get("/about")
def about():
    return {"About": "This is the response from About API Endpoint"}


@app.get("/patients")
def view():
    data = load_data()
    return data


@app.get("/patients/{patient_id}")
def view_patient(
    patient_id: str = Path(..., description="ID of the patient", example="P001")
):
    data = load_data()

    if patient_id in data:
        return data[patient_id]
    else:
        raise HTTPException(status_code=404, detail="Patient not found")


@app.get("/sort")
def sort_patients(
    sort_by: str = Query(..., description="Sort by Height, Weight, Bmi"),
    order: str = Query("asc", description="Order in Asc or Desc"),
):
    valid_feilds = ["height", "weight", "bmi"]
    if sort_by not in valid_feilds:
        raise HTTPException(
            status_code=404, detail=f"Invalid field selected from {valid_feilds}"
        )
    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=404, detail=f"Invalid selction between asc and desc"
        )
    data = load_data()
    sort_order = True if order == "desc" else False

    sorted_data = sorted(
        data.values(), key=lambda x: x.get(sort_by, 0), reverse=sort_order
    )
    return sorted_data


@app.post("/create")
def create_patient(patient: Patient):
    # Load the data first
    data = load_data()

    # Check if the patient already exists
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient already exists")

    # Add the patient to the database
    data[patient.id] = patient.model_dump(exclude=["id"])

    save_data(data)

    return JSONResponse(
        status_code=201, content={"Message": "Patient created successfully"}
    )


@app.put("/edit/{patient_id}")
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    existing_patient_info = data[patient_id]

    updated_patient_info = patient_update.model_dump(exclude_unset=True)

    for key, value in updated_patient_info.items():
        existing_patient_info[key] = value

    existing_patient_info["id"] = patient_id
    # Converting Existing patient object to Pydantic Object to calculate updated bmi and verdict
    patient_pydantic_object = Patient(**existing_patient_info)
    # Converting Pydantic Object to dict
    existing_patient_info = patient_pydantic_object.model_dump(exclude="id")
    # Add this dict to data
    data[patient_id] = existing_patient_info
    # Save data
    save_data(data)
    return JSONResponse(
        status_code=200, content={"Message": "Patient details updated successfully"}
    )


@app.delete("/patient/{patient_id}")
def delete_patient(patient_id: str):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    del data[patient_id]
    save_data(data)
    return JSONResponse(
        status_code=200, content={"Message": "Patient deleted successfully"}
    )
