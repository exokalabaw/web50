from .models import Tag, Quiz, Bookmark, Follow
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .forms import QuizForm, QuizEditForm
from django.shortcuts import render, redirect


def isowner(owner, currentuser):
    if owner == currentuser:
        return True
    else:
        return False
# assuming pagetypes are public, user, bookmarked, tag, following
def plok(request, ptid, pagetype):
#if the page type is a tag, the id is the tag id, if the page type is a user's or an id the id is the user id
    if pagetype =="public":
        qs = Quiz.objects.filter(private = False)
    elif pagetype == "user":
        if isowner(ptid, request.user.id):
            qs = Quiz.objects.filter(owner_id =request.user.id)
        else:
            qs = Quiz.objects.filter(owner_id = ptid, private = False)
    
    
    elif pagetype == "bookmarked":
        bookmarks = Bookmark.objects.filter(owner_id = request.user.id)
        bids = []
        for b in bookmarks:
            bids.append(b.quiz_id)
        qs = Quiz.objects.filter(id__in = bids, private = False)

    elif pagetype == "following":
        following = Follow.objects.filter(follower_id = request.user.id)
        fids = []
        for f in following:
            fids.append(f.followee_id)
        qs = Quiz.objects.filter(owner_id__in = fids, private = False)
    elif pagetype == "tag":
        tagged = Tag.objects.get(id = ptid)
        g = tagged.tags.all()
        qs = g

    
        

    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    has_next = page_obj.has_next()
    has_previous = page_obj.has_previous()
    end_index = paginator.num_pages
    plists = [quiz.serialize() for quiz in page_obj]
    for p in plists:
        bookmarked = Bookmark.objects.filter(quiz_id=p['id'], owner=request.user.id).count()
        p['bookmarked']=bookmarked
    print(plists)
    r = {'posts':plists,'has_next':has_next,'has_previous':has_previous,'end':end_index}
    return r

def validpage(request, type):
    if type == "public" or type == "tag":
        return True
    elif type == "user" or type == "bookmarked" or type == "following":
        if  request.user.is_authenticated:
            return True
        else:
            return False
    else:
        return False
def sortAnswerIds(question):
    l = []
    for q in question['answers']:
        if q['is_correct']:
            l.append(q['id'])
    return l
def sortPossibleAnswers(question):
    b = []
    for h in question['answers']:
        b.append(h['possible_answer'])
    return b
def sortCorrectAnswerStrings(question):
    h = []
    for n in question['answers']:
        if n["is_correct"]:
            h.append(n['possible_answer'])
    return h
def findUserAnswer(question_id, answer_items):
    r = []
    for i in answer_items:
        if i['question_id'] == question_id:
            r = i['answers']
    return r
def findUserAnswerIDS(question_id, answer_items):
    r = []
    for i in answer_items:
        if i['question_id'] == question_id:
            r = i['answerids']
    return r
def processTXT(pa, ua):
    l = len(ua)
    if l >= 1:
        for a in pa:
            if a == ua[0]:
                return True
    return False
def processMCOA(ai, ua):
    if ai[0] == ua[0]:
            return True
    return False
def processOA(ai, ua):
    for i in range(len(ai)): 
        if ai[i] != ua[i]:
            return False
    return True
# this needs fixing
def processMCMA(ai, ua):
    #run through all of the possible answers and see if any of the user answers is correct.. if there are none, return
    
    kl = len(ai)
    ul = len(ua)
    
    if len(ai) != len(ua):
        return False
    else:
        ai.sort()
        ua.sort()
        for i in range(len(ai)):
            if ai[i] != ua[i]:
                return False
        return True
#for when the user adds or edits the category field in a quiz
def returnTagIds(t):
    inputarray = []
    idarray = []
    namearray = []
    newnames = []
    newids = []
    res = [word.strip().lower() for word in t.split(",")]
    print(f"res is {res}")
    tagsreturn = Tag.objects.filter(name__in=res)
    for h in res:
        inputarray.append(h)
    for tag in tagsreturn:
        idarray.append(tag.id)
        namearray.append(tag.name)
    for k in inputarray:
        if k not in namearray:
            newnames.append(k)
            new = Tag(name=k)
            new.save()
            idarray.append(new.id)

    return idarray

def processSave(request):
    p = request.POST
        # copy the querydict to make it mutable
    g = p.copy()
    # since the form can't validate on the input values, even on empty input, remove the tag attribute
    g.pop('tag')
    # empty array for tag numbers
    tagarray = []
    # if the user input something on the field
    if p['tag']:
        # custom function to check on each of the comma separated values exist, if not, create, and then return a list of ids
        tagarray = returnTagIds(p['tag'])
        g['tag'] = tagarray
    # you can now return a form that will validate
    returndata = QuizForm(g)
    # f = { "form" : returndata , "type" : "Add", "user_id": request.user.id} 
    if returndata.is_valid():
        s = returndata.save(commit=False)
        s.owner_id = request.user.id
        s.save()
        returndata.save_m2m()
        form  = QuizForm(instance=s)
    return redirect(f"/edit/{s.id}?success=saved")