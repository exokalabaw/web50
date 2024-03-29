import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from .models import User, Tag, Quiz, Quiz_item, Answer_item, Quiz_history, Bookmark, Follow
from .forms import QuizForm, QuizEditForm
from .helpers import plok, isowner, validpage, processMCOA, processOA, processTXT, processMCMA, sortAnswerIds, sortPossibleAnswers, findUserAnswer, findUserAnswerIDS, sortCorrectAnswerStrings, returnTagIds, processSave, processEditQuestion
import random
# Create your views here.

def index(request):
    data = Quiz.objects.filter()
    return render(request, "kabisote/index.html", {'items': data})

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "kabisote/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "kabisote/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "kabisote/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "kabisote/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "kabisote/register.html")
#add and edit quiz page views
def add(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            return processSave(request, None)
        else:

            form = QuizForm()
            f = { "form" : form , "type" : "Add", "user_id": request.user.id} 
            return render(request, "kabisote/addedit.html", f)
    else: 
        return redirect(f"/error-404")

def editdetails(request, id):
    if request.user.is_authenticated:
        quizs = Quiz.objects.filter(pk=id)
        if isowner(request.user.id,quizs[0].owner_id):
            if request.method == "POST":
                return processSave(request, id)
            else:
                form = QuizEditForm(instance=quizs[0])
                k = quizs[0].tagsastext()
                f = { "form" : form ,"tags":k, "type" : "Edit", "user_id": request.user.id,"id": id} 
                return render(request, "kabisote/addedit.html", f)
        else:
            return redirect(f"/error-404")
    else:
        return redirect(f"/error-404")
def edit(request, id):
    quiz = Quiz.objects.filter(pk=id)
    if len(quiz) == 0:
        return redirect("/error-404")
    else:
        if isowner(request.user.id, quiz[0].owner.id):
            qi = Quiz_item.objects.filter(quiz_id = id).order_by("question_number")
            quizitems = [item.serializeForEdit() for item in qi]
            return render(request, "kabisote/quiz.html", {"type":"edit", "quiz":quiz[0], "script": "editquiz","quizitems": quizitems})
        else:
            return redirect("/error-404")
   
        
def delete(request, id):
    quiz = Quiz.objects.filter(pk=id)
    if len(quiz) == 0:
        return redirect("/error-404")
    else:
        if isowner(request.user.id, quiz[0].owner.id):
            quiz.delete()
            return redirect(f"/quizzes/user/{request.user.id}?success=deleted")
        else:
            return redirect(f"/error-404")   
#questions and answers api
# teaser pages    
# pagetypes are public, user, bookmarked, tag, following
def api(request, type):
    if validpage(request, type):
        posts = plok(request, None, type)
        return JsonResponse(posts, safe=False)
    else:
        return JsonResponse({"error":"this is not allowed"}, safe=False)

def apiwid(request, type, id):
    if validpage(request, type):
        posts = plok(request, id, type)
        return JsonResponse(posts, safe=False)
    else:
        return JsonResponse({"error":"this is not allowed"}, safe=False)
    
#add and edit questions api
@login_required
def questionsapi(request):
    r = json.loads(request.body)
    
    if r['addoredit'] == 'add':
        lastqn = Quiz_item.objects.filter(quiz_id=r['quizid']).values('question_number').reverse()[:1]
        lastqnlen = len(lastqn)
        if lastqnlen == 0:
            next_number = 1
        else:
            next_number = lastqn[0]['question_number'] +1
        print(r['answers'])
        questionitem = Quiz_item(quiz_id=r['quizid'], question=r['question'], question_number=next_number, quiz_type=r['type'])
        questionitem.save()
        for item in r['answers']:
            newanswer = Answer_item(possible_answer=item['possible_answer'],is_correct=item['is_correct'], answer_weight=item['answer_weight'])
            questionitem.answer_item_set.add(newanswer, bulk=False)
            print(f"items {newanswer}")
        questionitem.save()
        print(f'the whole thing: {questionitem}')
    else:
        questionitem = Quiz_item.objects.get(pk=r['question_id'])
        processEditQuestion(request, questionitem, r)
        print(questionitem.question)
            # questionitem.answer_item_set.add(possible_answer=item['possible_answer'])
    # print(questionitem)
    # receive your question and answers via POST here
    qi = Quiz_item.objects.filter(quiz_id = r['quizid']).order_by("question_number")
    quizitems = [item.serializeForEdit() for item in qi]
    return JsonResponse(quizitems, safe=False)
@login_required
def deletequestion(request):
    p = json.loads(request.body)

    q = Quiz_item.objects.get(pk=p['questionid'])
    quizid = q.quiz_id
    q.delete()

    qi = Quiz_item.objects.filter(quiz_id = quizid).order_by("question_number")
    quizitems = [item.serializeForEdit() for item in qi]
    print(f"quizitems = {quizitems}")
    return JsonResponse(quizitems, safe=False)
# quizzes / public, user/<int:id>, bookmarked/<int:id>, following/<int:id>, tag/<int:id> 
def routes(request, type):
    if validpage(request, type):
        return render(request, "kabisote/teasers.html", {"type": type, "id": request.user.id, "script": "teasers"})
    else:
        return redirect(f"/error-404")
def routesnid(request, type, id):
    if validpage(request, type):
        tag = None
        u = None
        if type == "tag":
            t = Tag.objects.get(pk=id)
            tag = t.name
        if type == "user":
            u = User.objects.get(pk=id)
        #set a title and pass it depending on the page
        return render(request, "kabisote/teasers.html", {"type": type, "id": id,"script": "teasers", "tag":tag, "username":u})
    else:
        return redirect(f"/error-404")
    
def quiz(request, id):
    quiz = Quiz.objects.get(pk=id)
    qi = Quiz_item.objects.filter(quiz_id = id).order_by("question_number")
    bm = Bookmark.objects.filter( quiz_id = id, owner = request.user.id)
    
    
    if len(bm) >= 1:
        bookmarked = 1
    else:
        bookmarked = 0
    quizitems = [item.serialize() for item in qi]


    return render(request, "kabisote/quiz.html", {"quiz":quiz, "type": "quiz", "script": "quiz", "quizitems": quizitems, "bookmarked": bookmarked})
#if isfollowing id should be the id of the follow object, if not following the id is the id of the followee
def tf(request, isfollowing, id):
    #check if zero converts to 
    try:
        if isfollowing:
            r = Follow.objects.get(id=id)
            r.delete()
            return JsonResponse({"update":"deleted"}, safe=False)
        else:
            r = Follow(follower_id=request.user.id, followee_id=id)
            r.save()
            
            return JsonResponse({"update":"followed"}, safe=False)
        
    except:
    
        return JsonResponse({"update":"error"}, safe=False)
def tb(request, bookmarked, id):
    try:
        if bookmarked == "true":
            b = Bookmark.objects.get(quiz_id = id, owner_id=request.user.id)
            b.delete()
            return JsonResponse({"update":"deleted"}, safe=False)
        else:
            b = Bookmark(quiz_id=id, owner_id=request.user.id)
            b.save()
            return JsonResponse({"update":"saved"}, safe=False)
    except:
        return JsonResponse({"update":"error"}, safe=False)

def checkanswers(request):
    if request.method == "POST":
        r = json.loads(request.body)
        # query for the answer key data
        quizid = r['quizid']
        savequestions = Quiz_item.objects.filter(quiz_id = quizid)
        questions = [item.answer_key() for item in savequestions]
        # user answers
        
        answer_items = r['answers']
        max_score = 0
        user_score = 0
        answerset = []
        # loop through each answer key question 
        for question in questions:
            question_type = question['quiz_type']
            question_id =  question['id']
            user_answers = findUserAnswer(question_id, answer_items)
            user_answerids = findUserAnswerIDS(question_id, answer_items)
            points = question['points']
            max_score = max_score + points
            answer_strings = sortCorrectAnswerStrings(question)
    
            if question_type == "txt":
                correct_answers = sortPossibleAnswers(question)
                correct = processTXT(correct_answers, user_answers)
            else:
                correct_answers = sortAnswerIds(question)
                if question_type == "mcoa":
                    correct = processMCOA(correct_answers, user_answerids)
                elif question_type == "mcma":
                    correct = processMCMA(correct_answers, user_answerids)
                elif question_type == "oa":
                    correct = processOA(correct_answers, user_answers)
            if correct:
                user_score = user_score + points
            
            answer_data = {
                "answerstrings" : answer_strings,
                "answerids": user_answerids,
                "answers": user_answers,
                "question_type": question_type,
                "correct_answers": correct_answers,
                "question_id":question_id,
                "correct":correct,
                "points": points
                
            }
            answerset.append(answer_data)
            #this is where you stopped, if you did everything right, you should be able to create one big json array from this.. thats what you need to do next
            
        # add to json return that will have: in/correct, correct answers, user answers, maxpoints, user score, question id
        returnitem = {
            "user_answers":answerset,
            "score_max": max_score,
            "score_user": user_score,
            "quiz_id": quizid
        }
            
        print(returnitem)
        return JsonResponse(returnitem, safe=False)
    else:
        return JsonResponse({"error":"did not go through"}, safe=False)


@login_required
# i feel like this query is so expensive
def reorder(request):
    q = json.loads(request.body)
    quid = q[0]['quiz_id']
    savedQuestions = Quiz_item.objects.filter(quiz_id=quid)
    print(f'pre change savedq : {savedQuestions}')
    length = len(q)
    for item in q:
        id = item['id']
        qn = item['question_number']
        
        # question numbers are unique to the question so you have to check if the question's id number has not changed
        
        for question in savedQuestions:
            if question.question_number == qn: 
                if question.id != id:
                    length = length + 1
                    question.question_number = length
                    question.save()
    print(f'should have different ids : {savedQuestions}')    
    for i in q:
        id = i['id']
        qn = i['question_number']     
        for question in savedQuestions:
            if question.id == id:
                    question.question_number = qn
                    question.save()
    print(f"new order is : {savedQuestions}")
    qi = Quiz_item.objects.filter(quiz_id=quid)
    quizitems = [item.serializeForEdit() for item in qi]
    return JsonResponse(quizitems, safe=False)
        
def randomize(request):
    qs = Quiz.objects.filter(private = False)
    rd = random.choice(qs)
    print(rd.id)
    return redirect(f"/quiz/{rd.id}")

def error404(request):
    return render(request, "kabisote/error-404.html")
