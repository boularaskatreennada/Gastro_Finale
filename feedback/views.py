from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from restaurant.decorators import client_required
from .models import Review, Complaint, ComplaintStatus
from .forms import ReviewForm, ComplaintForm
from datetime import date

# View all reviews
def review_list(request):
    reviews = Review.objects.select_related('client').order_by('-date')
    return render(request, 'client/reviews.html', {'reviews': reviews})

@client_required
def add_feedback_or_complaint(request):
    feedback_form = ReviewForm()
    complaint_form = ComplaintForm()

    if request.method == 'POST':
        if 'submit_feedback' in request.POST:
            feedback_form = ReviewForm(request.POST)
            if feedback_form.is_valid():
                review = feedback_form.save(commit=False)
                review.client = request.user.client
                review.date = date.today()
                review.save()
                return redirect('review_list')

        elif 'submit_complaint' in request.POST:
            complaint_form = ComplaintForm(request.POST)
            if complaint_form.is_valid():
                complaint = complaint_form.save(commit=False)
                complaint.client = request.user.client
                complaint.date = date.today()
                complaint.status = ComplaintStatus.UNRESPONDED
                complaint.save()
                return redirect('review_list')

    return render(request, 'client/addFeedback.html', {
        'feedback_form': feedback_form,
        'complaint_form': complaint_form,
    })
