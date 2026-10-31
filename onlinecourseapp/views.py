
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from .models import Course, Enrollment, Submission, Choice


def course_details(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    return render(
        request,
        "course_details_bootstrap.html",
        {"course": course}
    )


def submit(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    questions = course.questions.all()

    if request.method == "POST":

        # Get the learner ID stored in the session.
        learner_id = request.session.get("learner_id")

        if not learner_id:
            return render(
                request,
                "mock_exam.html",
                {
                    "course": course,
                    "questions": questions,
                    "error": "Please log in or select a learner before submitting."
                }
            )

        # Retrieve the learner's enrollment in this course.
        enrollment = get_object_or_404(
            Enrollment,
            course=course,
            learner_id=learner_id
        )

        # Create a submission linked to the enrollment.
        submission = Submission.objects.create(
            enrollment=enrollment
        )

        selected_ids = []

        # Save the selected choices.
        for question in questions:
            selected_choice_id = request.POST.get(
                f"question_{question.id}"
            )

            if selected_choice_id:
                try:
                    selected_choice = Choice.objects.get(
                        id=int(selected_choice_id),
                        question=question
                    )

                    submission.choices.add(selected_choice)
                    selected_ids.append(selected_choice.id)

                except (Choice.DoesNotExist, ValueError):
                    continue

        # Redirect to the exam result page.
        return redirect(
            reverse(
                "show_exam_result",
                kwargs={
                    "course_id": course.id,
                    "submission_id": submission.id
                }
            )
        )

    return render(
        request,
        "mock_exam.html",
        {
            "course": course,
            "questions": questions
        }
    )


def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, id=course_id)

    submission = get_object_or_404(
        Submission,
        id=submission_id,
        enrollment__course=course
    )

    selected_ids = list(
        submission.choices.values_list("id", flat=True)
    )

    # Calculate the grade using the saved selected choices.
    grade = 0

    for question in course.questions.all():
        selected_choice = submission.choices.filter(
            question=question,
            is_correct=True
        ).first()

        if selected_choice:
            grade += question.grade

    return render(
        request,
        "exam_result_bootstrap.html",
        {
            "course": course,
            "selected_ids": selected_ids,
            "grade": grade,
            "submission": submission
        }
    )
