from pydantic import BaseModel, Field, field_validator

class UserInput(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    user_id: str = Field(min_length=1, max_length=80)
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=0, le=500)
    goal: str
    intensity: str

    @field_validator("goal")
    @classmethod
    def valid_goal(cls, value):
        allowed = {"general wellness", "strength", "flexibility", "cardiovascular fitness", "muscle gain"}
        if value not in allowed: raise ValueError("Choose a listed fitness goal")
        return value

    @field_validator("intensity")
    @classmethod
    def valid_intensity(cls, value):
        if value not in {"low", "medium", "high"}: raise ValueError("Invalid intensity")
        return value

class FeedbackRequest(BaseModel):
    user_id: str
    feedback: str = Field(min_length=3, max_length=1000)
