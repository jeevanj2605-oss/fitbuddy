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
            user_id=data.user_id,
            username=data.username,
            age=data.age,
            weight=data.weight,
            goal=data.goal,
            intensity=data.intensity,
        )

        db.add(user)

    else:
        # Update existing user information
        user.username = data.username
        user.age = data.age
        user.weight = data.weight
        user.goal = data.goal
        user.intensity = data.intensity

    db.commit()
    db.refresh(user)

    # -----------------------------------------------------
    # Generate AI Workout
    # -----------------------------------------------------

    plan_text = generate_workout_gemini(data)

    # Generate nutrition tip
    tip = generate_nutrition_tip_with_flash(data.goal)

    # -----------------------------------------------------
    # Save generated plan
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

    # Save revised plan and feedback
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
# HISTORY DASHBOARD
# ---------------------------------------------------------

@router.get("/history", response_class=HTMLResponse)
def history(
    request: Request,
    db: Session = Depends(get_db),
):
    # Get all users
    users = (
        db.query(User)
        .order_by(User.id.desc())
        .all()
    )

    # Get all plans
    plans = (
        db.query(Plan)
        .order_by(Plan.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "users": users,
            "plans": plans,
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

    # Get plans directly from Plan table.
    # This avoids relying on a User.plans relationship.
    plans = (
        db.query(Plan)
        .order_by(Plan.id.desc())
        .all()
    )

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
# API - HISTORY
# ---------------------------------------------------------

@router.get("/api/history")
def api_history(
    db: Session = Depends(get_db),
):
    plans = (
        db.query(Plan)
        .order_by(Plan.id.desc())
        .all()
    )

    return [
        {
            "id": plan.id,
            "user_id": plan.user_id,
            "original_plan": plan.original_plan,
            "updated_plan": plan.updated_plan,
            "nutrition_tip": plan.nutrition_tip,
            "feedback": plan.feedback,
            "created_at": plan.created_at,
        }
        for plan in plans
    ]


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@router.get("/health")
def health():
    return {
        "status": "ok"
    }