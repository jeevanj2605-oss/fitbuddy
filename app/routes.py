from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User, Plan
from app.schemas import UserInput
from app.ai import (
    generate_workout_gemini,
    generate_nutrition_tip_with_flash,
    update_workout_plan,
)

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


# ---------------------------------------------------------
# GENERATE WORKOUT
# ---------------------------------------------------------

@router.post("/generate-workout", response_class=HTMLResponse)
def generate(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    # Validate user input
    try:
        data = UserInput(
            username=username.strip(),
            user_id=user_id.strip(),
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )

    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(exc)
            },
            status_code=422,
        )

    # -----------------------------------------------------
    # Find existing user
    # -----------------------------------------------------

    user = (
        db.query(User)
        .filter_by(user_id=data.user_id)
        .first()
    )

    # If user doesn't exist, create new user
    if not user:
        user = User(
            user_id=data.user_id
        )

        db.add(user)

    # Update user information
    for field, value in data.model_dump().items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    # -----------------------------------------------------
    # Generate AI Workout
    # -----------------------------------------------------

    plan_text = generate_workout_gemini(data)

    # Generate nutrition tip
    tip = generate_nutrition_tip_with_flash(data.goal)

    # -----------------------------------------------------
    # Save plan
    # -----------------------------------------------------

    plan = Plan(
        user_id=data.user_id,
        original_plan=plan_text,
        nutrition_tip=tip,
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    # -----------------------------------------------------
    # Show result
    # -----------------------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "user": user,
            "plan": plan,

            # IMPORTANT:
            # Plan model has original_plan, not original_plan_text
            "workout_plan": plan.original_plan,

            "nutrition_tip": plan.nutrition_tip,
            "updated": False,
        },
    )


# ---------------------------------------------------------
# SUBMIT FEEDBACK
# ---------------------------------------------------------

@router.post("/submit-feedback", response_class=HTMLResponse)
def feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    # Find user
    user = (
        db.query(User)
        .filter_by(user_id=user_id)
        .first()
    )

    # Find latest plan
    plan = (
        db.query(Plan)
        .filter_by(user_id=user_id)
        .order_by(Plan.id.desc())
        .first()
    )

    # User or plan not found
    if not user or not plan:
        raise HTTPException(
            status_code=404,
            detail="User or plan not found. Generate a plan first.",
        )

    # -----------------------------------------------------
    # Update workout using AI
    # -----------------------------------------------------

    revised = update_workout_plan(
        plan.updated_plan or plan.original_plan,
        feedback,
        user.goal,
        user.intensity,
    )

    # Save revised plan
    plan.updated_plan = revised
    plan.feedback = feedback

    db.commit()
    db.refresh(plan)

    # -----------------------------------------------------
    # Show updated result
    # -----------------------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "user": user,
            "plan": plan,
            "workout_plan": revised,
            "nutrition_tip": plan.nutrition_tip,
            "updated": True,
        },
    )


# ---------------------------------------------------------
# VIEW ALL USERS
# ---------------------------------------------------------

@router.get("/view-all-users", response_class=HTMLResponse)
def all_users(
    request: Request,
    db: Session = Depends(get_db),
):
    users = (
        db.query(User)
        .order_by(User.id.desc())
        .all()
    )

    plans = [
        plan
        for user in users
        for plan in user.plans
    ]

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "users": users,
            "plans": plans,
        },
    )


# ---------------------------------------------------------
# API - ALL USERS
# ---------------------------------------------------------

@router.get("/api/users")
def api_users(
    db: Session = Depends(get_db),
):
    return [
        {
            "user_id": user.user_id,
            "username": user.username,
            "age": user.age,
            "goal": user.goal,
            "intensity": user.intensity,
        }
        for user in db.query(User).all()
    ]


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@router.get("/health")
def health():
    return {
        "status": "ok"
    }