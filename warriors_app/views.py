from rest_framework import serializers, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from .models import *
from django.http import HttpResponse, JsonResponse
from secrets import token_urlsafe


class WarriorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warrior
        fields = "__all__"


class SkillRelatedSerializer(serializers.ModelSerializer):
    warrior_skils = WarriorSerializer(many=True)

    class Meta:
        model = Skill
        fields = ["title", "warrior_skils"]


class WarriorRelatedSerializer(serializers.ModelSerializer):
    skill = serializers.SlugRelatedField(read_only=True, many=True, slug_field='title')

    # skill = serializers.StringRelatedField(read_only=True, many=True)

    class Meta:
        model = Warrior
        fields = "__all__"


class WarriorDepthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warrior
        fields = "__all__"

        # добавляем глубину
        depth = 1


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = "__all__"


class ProfessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = "__all__"


class WarriorNestedSerializer(serializers.ModelSerializer):
    # делаем наследование
    profession = ProfessionSerializer()
    skill = SkillSerializer(many=True)

    # уточняем поле
    race = serializers.CharField(source="get_race_display", read_only=True)

    class Meta:
        model = Warrior
        fields = "__all__"


class WarriorAPIView(APIView):
    def get(self, request):
        warriors = Warrior.objects.all()
        serializer = WarriorNestedSerializer(warriors, many=True)
        # serializer = WarriorSerializer(warriors, many=True)
        return Response({"Warriors": serializer.data})


class ProfessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = "__all__"


class ProfessionCreateView(APIView):
    def post(self, request):
        profession = request.data.get("profession")
        serializer = ProfessionCreateSerializer(data=profession)

        if serializer.is_valid(raise_exception=True):
            profession_saved = serializer.save()

        return Response({"Success": "Profession '{}' created succesfully.".format(profession_saved.title)})


class SkillAPIView(APIView):
    def get(self, request):
        skills = Skill.objects.all()
        serializer = SkillSerializer(skills, many=True)
        return Response({"Skills": serializer.data})


class SkillCreateView(APIView):
    def post(self, request):
        skill = request.data.get("skill")
        serializer = SkillSerializer(data=skill)

        if serializer.is_valid(raise_exception=True):
            skill_saved = serializer.save()

        return Response({"Success": "Skill '{}' created succesfully.".format(skill_saved.title)})


class SkillWarriorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillOfWarrior
        fields = "__all__"


class WarriorCreateSerializer(serializers.ModelSerializer):
    race = serializers.CharField(max_length=1)
    name = serializers.CharField(max_length=120)
    # level = serializers.CharField(max_length=120, default=0)
    profession = serializers.PrimaryKeyRelatedField(queryset=Profession.objects.all())
    skill = SkillSerializer(many=True, read_only=True, source='skill.title')

    class Meta:
        model = Warrior
        fields = "__all__"

    # def create(self, validated_data):
    #     print(validated_data)
    #     warrior = Warrior(**validated_data)
    #     warrior.save()
    #
    #     return Warrior(**validated_data)


# class WarriorCreateSerializer(serializers.ModelSerializer):
#
#     profession_title = serializers.RelatedField(source='profession', read_only=True)
#     skill_title = serializers.RelatedField(source='skill', read_only=True)
#
#     class Meta:
#         model = Warrior
#         fields = ["race","name","level","skill_title","profession_title"]
#         # fields = "__all__"


class WarriorCreateView(generics.CreateAPIView):
    serializer_class = WarriorCreateSerializer
    queryset = Warrior.objects.all()

    # permission_classes = [permissions.AllowAny]

    # def perform_create(self, serializer):
    #     serializer.save(owner=self.request.user)


class WarriorProfessionAPIView(APIView):
    def get(self, request):
        warriors = Warrior.objects.all()
        profession = Profession.objects.all()
        warrior_serializer = WarriorSerializer(warriors, many=True)
        profession_serializer = ProfessionSerializer(profession, many=True)
        return Response({"Warriors": warrior_serializer.data, "Professions": profession_serializer.data})


class WarriorSkillAPIView(APIView):
    def get(self, request):
        warriors = Warrior.objects.all()
        skill = Skill.objects.all()
        warrior_serializer = WarriorSerializer(warriors, many=True)
        skill_serializer = SkillSerializer(skill, many=True)
        return Response({"Warriors": warrior_serializer.data, "Skills": skill_serializer.data})


class SingleWarriorSerializer(serializers.ModelSerializer):
    profession = ProfessionSerializer()
    skill = SkillSerializer(many=True)

    class Meta:
        model = Warrior
        fields = "__all__"
        read_only_fields = ['id']


class SingleWarriorView(generics.RetrieveAPIView):
    serializer_class = SingleWarriorSerializer
    queryset = Warrior.objects.all()


class WarriorUpdateView(generics.UpdateAPIView):
    queryset = Warrior.objects.all()
    serializer = WarriorSerializer
    lookup_field = 'pk'


class WarriorDestroyView(generics.DestroyAPIView):
    queryset = Warrior.objects.all()
    serializer = WarriorSerializer


# user_name = "timon"
# password = "12345"


def authview(request):
    username = request.GET.get('username')
    password = request.GET.get('password')
    user = User.objects.filter(username=username, password=password)
    if user.count() == 0:
        return JsonResponse({'Error': 'Unauthorized'})
    else:
        user = user[0]
        token = token_urlsafe(10)
        auth_token = User_token(user_id=user, auth_token=token)
        auth_token.save()
        print(token)
        return JsonResponse({'auth_token': token, 'user_id': user.id})


def userview(request):
    token = request.headers['Authorization'].split()[1]
    user_current = User_token.objects.filter(auth_token=token)
    user_id = user_current[0].user_id.id
    if request.method == 'GET':
        return JsonResponse({'id': user_id, 'username': user_current[0].user_id.username,
                             'password': user_current[0].user_id.password,
                             'first_name': user_current[0].user_id.first_name,
                             'last_name': user_current[0].user_id.last_name,
                             'tel': user_current[0].user_id.tel})
    elif request.method == 'POST':
        user = User.objects.filter(username=request.POST.get('username'))
        if user.count() == 0 or user.count() == 1 and user_current[0].user_id.username == user[0].username:
            User.objects.filter(id=user_id).update(username=request.POST.get('username'), password=request.POST.get('password'),
                          first_name=request.POST.get('first_name'),
                          last_name=request.POST.get('last_name'),
                          tel=request.POST.get('tel'))
        else:
            return JsonResponse({'Error': 'Username is already taken'})
    return JsonResponse({'id': user_id})


def signinview(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    tel = request.POST.get('tel')

    if request.method == 'POST' and username is not None and password is not None and first_name is not None \
            and last_name is not None and tel is not None:
        user = User.objects.filter(username=username)
        if user.count() == 0:
            user = User(username=username, password=password, first_name=first_name, last_name=last_name, tel=tel)
            user.save()
            token = token_urlsafe(10)
            auth_token = User_token(user_id=user, auth_token=token)
            auth_token.save()
            return JsonResponse({'auth_token': token, 'user_id': user.id})
        else:
            return JsonResponse({'Error': 'Username is already taken'})
    else:
        return JsonResponse({'Error': 'Incorrect data'})
