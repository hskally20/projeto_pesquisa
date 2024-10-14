from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from braces.views import GroupRequiredMixin
from django.urls import reverse_lazy
from .models import Hospital, Medico, Paciente, Cronograma, Consulta, Comentario, Triagem, Notificacao
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import render, get_object_or_404
# cadastros/views.py

from django.http import JsonResponse
from django.views import View
import json
from .models import Paciente, Notificacao
from django.contrib.auth.mixins import LoginRequiredMixin

class ChamarPacienteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                paciente_id = data.get("paciente_id")

                if not paciente_id:
                    return JsonResponse({"success": False, "message": "Paciente ID não fornecido."})

                try:
                    paciente = Paciente.objects.get(id=paciente_id)
                except Paciente.DoesNotExist:
                    return JsonResponse({"success": False, "message": "Paciente não encontrado."})

                if paciente.usuario_cadastrador != request.user:
                    return JsonResponse({"success": False, "message": "Você não tem permissão para chamar esse paciente."})

                mensagem = f'O médico está chamando o paciente {paciente.nome}.'

                try:
                    notificação = Notificacao.objects.create(paciente=paciente.usuario_cadastrador, mensagem=mensagem)
                except Exception as e:
                    return JsonResponse({"success": False, "message": f"Erro ao salvar notificação: {str(e)}"})

                return JsonResponse({"success": True, "message": "Notificação enviada!"})

            except json.JSONDecodeError:
                return JsonResponse({"success": False, "message": "Erro ao processar requisição."})

        return JsonResponse({"success": False, "message": "Erro ao processar requisição."})


# <=============== usuários ==============>


class HospitalCreate(GroupRequiredMixin, CreateView):
    group_required = u"Admin"
    login_url = reverse_lazy('login')
    model = Hospital
    fields = ['nome', 'descricao']
    template_name = 'form.html'
    success_url = reverse_lazy('listar-hospital')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['Titulo'] = 'Cadastro de Hospitais '
        return context

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class MedicoCreate(GroupRequiredMixin, CreateView):
    group_required = u"Admin"
    login_url = reverse_lazy('login')
    model = Medico
    fields = ['numero', 'nome', 'cpf', 'especificacao', 'hospital']
    template_name = 'form.html'
    success_url = reverse_lazy('listar-medico')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['Titulo'] = 'Cadastro de Médicos '
        return context

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class PacienteCreate(GroupRequiredMixin, CreateView):
    group_required = u'Paciente'
    login_url = reverse_lazy('login')
    model = Paciente
    fields = ['telefone', 'nome', 'numero_sus', 'hospital', 'doença_cronica', 'sintomas', 'idade', 'usuario_cadastrador']
    template_name = 'form.html'
    success_url = reverse_lazy('Listar-paciente')

    def form_valid(self, form):
        if form.instance.idade < 59:
            form.instance.descricao = 'comun'
            if form.instance.doença_cronica == '' or form.instance.doença_cronica is None:
                form.instance.descricao = 'comun'
            else:
                form.instance.descricao = 'preferencial'
        else:
            form.instance.descricao = 'preferencial'
        form.instance.usuario = self.request.user
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['Titulo'] = 'Cadastro de Pacientes '
        context['conteudo'] = 'Se não tem doença crônica, não preencha o campo abaixo!'
        return context


class TriagemCreate(GroupRequiredMixin, CreateView):
    group_required = u'Medico'
    login_url = reverse_lazy('login')
    model = Triagem
    fields = ['data', 'horario', 'pressao', 'hospital', 'medico', 'paciente']
    template_name = 'form.html'
    success_url = reverse_lazy('Listar-triagem')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['Titulo'] = 'Cadastro de Triagens'
        context['conteudo'] = 'Preencha todos os campos'
        return context


# Update
class HospitalUpdate(GroupRequiredMixin, UpdateView):
    group_required = u"Admin"
    login_url = reverse_lazy('login')
    model = Hospital
    fields = ['nome', 'descricao']
    template_name = 'form.html'
    success_url = reverse_lazy('listar-hospital')

    def get_object(self, query=None):
        self.object = Hospital.objects.get(pk=self.kwargs['pk'], usuario=self.request.user)
        return self.object


class MedicoUpdate(GroupRequiredMixin, UpdateView):
    group_required = u"Admin"
    model = Medico
    fields = ['numero', 'nome', 'cpf', 'especificacao', 'hospital']
    template_name = 'form.html'
    success_url = reverse_lazy('inicio')

    def get_object(self, query=None):
        self.object = Medico.objects.get(pk=self.kwargs['pk'], usuario=self.request.user)
        return self.object


class PacienteUpdate(GroupRequiredMixin, UpdateView):
    group_required = u"Paciente"
    model = Paciente
    fields = ['telefone', 'nome', 'numero_sus', 'hospital', 'doença_cronica', 'sintomas', 'idade']
    template_name = 'form.html'
    success_url = reverse_lazy('Listar-paciente')

    def get_object(self, query=None):
        self.object = Paciente.objects.get(pk=self.kwargs['pk'], usuario=self.request.user)
        return self.object

    def form_valid(self, form):
        if form.instance.idade < 59:
            form.instance.descricao = 'comun'
            if form.instance.doença_cronica == '' or form.instance.doença_cronica is None:
                form.instance.descricao = 'comun'
            else:
                form.instance.descricao = 'preferencial'
        else:
            form.instance.descricao = 'preferencial'
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class TriagemUpdate(GroupRequiredMixin, UpdateView):
    group_required = u"Medico"
    model = Triagem
    fields = ['paciente', 'data', 'medico', 'hospital', 'horario', 'pressao']
    template_name = 'form.html'
    success_url = reverse_lazy('listar-triagem')

    def get_object(self, query=None):
        self.object = Triagem.objects.get(pk=self.kwargs['pk'], usuario=self.request.user)
        return self.object

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['Titulo'] = 'Cadastro de Triagens'
        context['conteudo'] = 'Preencha todos os campos'
        return context


# Delete
class HospitalDelete(GroupRequiredMixin, DeleteView):
    group_required = u"Admin"
    login_url = reverse_lazy('login')
    model = Hospital
    template_name = 'form-excluir.html'
    success_url = reverse_lazy('listar-hospital')

    def get_object(self, query=None):
        self.object = Hospital.objects.get(pk=self.kwargs['pk'], usuario=self.request.user)
        return self.object


class MedicoDelete(GroupRequiredMixin, DeleteView):
    group_required = u"Admin"
    model = Medico
    template_name = 'form-excluir.html'
    success_url = reverse_lazy('inicio')

    def get_object(self, query=None):
        self.object = Medico.objects.get(pk=self.kwargs['pk'], usuario=self.request.user)
        return self.object


class PacienteDelete(GroupRequiredMixin, DeleteView):
    group_required = u'Paciente'
    model = Paciente
    template_name = 'form-excluir.html'
    success_url = reverse_lazy('Listar-paciente')

    def get_object(self, query=None):
        self.object = Paciente.objects.get(pk=self.kwargs['pk'], usuario=self.request.user)
        return self.object


class TriagemDelete(GroupRequiredMixin, DeleteView):
    group_required = u'Medico' 
    login_url = reverse_lazy('login')
    model = Triagem
    template_name = 'form-excluir.html'
    success_url = reverse_lazy('Listar-triagem')

    def get_object(self, query=None):
        self.object = Triagem.objects.get(pk=self.kwargs['pk'], usuario=self.request.user)
        return self.object

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['Titulo'] = 'Exclusão de Triagens'
        context['conteudo'] = 'Tem certeza que deseja excluir esta triagem?'
        return context


# List
class HospitalList(GroupRequiredMixin, ListView):
    group_required = u'Admin'
    login_url = reverse_lazy('login')
    model = Hospital
    template_name = 'listas/hospital.html'
    paginate_by = 5

    def get_queryset(self):
        nome = self.request.GET.get('nome')
        if nome:
            hospital = Hospital.objects.filter(nome__icontains=nome)
        else:
            hospital = Hospital.objects.all()
        return hospital


class MedicoList(GroupRequiredMixin, ListView):
    group_required = u'Medico'
    login_url = reverse_lazy('login')
    model = Medico
    template_name = 'listas/medico.html'
    paginate_by = 5

    def get_queryset(self):
        nome = self.request.GET.get('nome')
        if nome:
            medico = Medico.objects.filter(nome__icontains=nome)
        else:
            medico = Medico.objects.all()
        return medico



class PacienteList(LoginRequiredMixin, ListView):
    model = Paciente
    template_name = 'listas/paciente.html'
    paginate_by = 5

    def get_queryset(self):
        nome = self.request.GET.get('nome')
        if nome:
            return Paciente.objects.filter(nome__icontains=nome)
        return Paciente.objects.all()


    def post(self, request, *args, **kwargs):
        # Verifica se a requisição é AJAX (pelo cabeçalho X-Requested-With)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            paciente_id = request.POST.get("paciente_id")  # ID do paciente chamado
            if not paciente_id:
                return JsonResponse({"success": False, "message": "Paciente ID não fornecido."})

            # Verifica se o paciente existe
            try:
                paciente = Paciente.objects.get(id=paciente_id)
            except Paciente.DoesNotExist:
                return JsonResponse({"success": False, "message": "Paciente não encontrado."})

            # Verifica se o usuário autenticado é o responsável pelo paciente
            if paciente.usuario_cadastrador != request.user:
                return JsonResponse({"success": False, "message": "Você não tem permissão para chamar esse paciente."})

            # Cria a notificação para o usuário que cadastrou o paciente
            mensagem = f'O médico está chamando o paciente {paciente.nome}.'
            try:
                Notificacao.objects.create(paciente=paciente.usuario_cadastrador, mensagem=mensagem)
            except Exception as e:
                return JsonResponse({"success": False, "message": f"Erro ao salvar notificação: {str(e)}"})

            return JsonResponse({"success": True, "message": "Notificação enviada!"})
        
        return JsonResponse({"success": False, "message": "Erro ao processar requisição."})

class TriagemList(GroupRequiredMixin, ListView):
    group_required = u'Medico'
    login_url = reverse_lazy('login')
    model = Triagem
    template_name = 'listas/triagem.html'
    paginate_by = 5

    def get_queryset(self):
        nome = self.request.GET.get('nome')
        if nome:
            triagem = Triagem.objects.filter(paciente__nome__icontains=nome)
        else:
            triagem = Triagem.objects.all()
        return triagem
    

class NotificacaoList(LoginRequiredMixin, ListView):
    model = Notificacao
    template_name = 'listas/notificacoes_paciente.html'
    context_object_name = 'notificacoes'

    def get_queryset(self):
        # Retorna as notificações do usuário logado
        return Notificacao.objects.filter(paciente=self.request.user)


# <================   funções do site   ==================>


class CronogramaCreate(GroupRequiredMixin, CreateView):
    group_required = u"Medico"
    login_url = reverse_lazy('login')
    model = Cronograma
    fields = ['nome', 'data', 'medico', 'hospital', 'horario']
    template_name = 'form.html'
    success_url = reverse_lazy('Listar-cronograma')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['Titulo'] = 'Cadastro de Cronogramas '
        return context

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class CronogramaDelete(GroupRequiredMixin, DeleteView):
    group_required = u"Medico"
    model = Cronograma
    template_name = 'form-excluir.html'
    success_url = reverse_lazy('Listar-cronograma')

    def get_object(self, query=None):
        self.object = Cronograma.objects.get(pk=self.kwargs['pk'], usuario=self.request.user)
        return self.object


class CronogramaUpdate(GroupRequiredMixin, UpdateView):
    group_required = u"Medico"
    login_url = reverse_lazy('login')
    model = Cronograma
    fields = ['paciente', 'data', 'medico', 'hospital', 'horario', 'pressao']
    template_name = 'form.html'
    success_url = reverse_lazy('Listar-cronograma')

    def get_object(self, query=None):
        self.object = Cronograma.objects.get(pk=self.kwargs['pk'], usuario=self.request.user)
        return self.object


class CronogramaList(ListView):
    model = Cronograma
    template_name = 'listas/cronograma.html'
    paginate_by = 5

    def get_queryset(self):
        nome = self.request.GET.get('nome')
        if nome:
            cronograma = Cronograma.objects.filter(nome__icontains=nome)
        else:
            cronograma = Cronograma.objects.all()
        return cronograma


class ConsultaCreate(CreateView):
    login_url = reverse_lazy('login')
    model = Consulta
    fields = ['paciente', 'data', 'medico', 'hospital', 'horario']
    template_name = 'form.html'
    success_url = reverse_lazy('Listar-consulta')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['Titulo'] = 'Agendar Consulta'
        return context

    def form_valid(self, form):
        if form.instance.status is None or form.instance.status == 'None':
            form.instance.status = 'pendente'
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class ConsultaDelete(DeleteView):
    model = Consulta
    template_name = 'form-excluir.html'
    success_url = reverse_lazy('Listar-consulta')

    def get_object(self, query=None):
        self.object = Consulta.objects.get(pk=self.kwargs['pk'], usuario=self.request.user)
        return self.object


class ConsultaUpdate(UpdateView):
    model = Consulta
    fields = ['paciente', 'data', 'medico', 'hospital', 'horario']
    template_name = 'form.html'
    success_url = reverse_lazy('Listar-consulta')

    def get_object(self, query=None):
        self.object = Consulta.objects.get(pk=self.kwargs['pk'], usuario=self.request.user)
        return self.object

    def form_valid(self, form):
        if form.instance.status is None or form.instance.status == 'None':
            form.instance.status = 'pendente'
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class Consulta2Update(UpdateView):
    model = Consulta
    fields = ['status']
    template_name = 'form.html'
    success_url = reverse_lazy('Listar-consulta')


class ConsultaList(ListView):
    login_url = reverse_lazy('login')
    model = Consulta
    template_name = 'listas/consulta.html'
    paginate_by = 5

    def get_queryset(self):
        consultas = Consulta.objects.all().order_by('data')
        lista_consultas_ordenada = []
        consultas_comuns = []
        consultas_preferenciais = []

        for consulta in consultas:
            if consulta.paciente.descricao == 'preferencial':
                consultas_preferenciais.append(consulta)
            else:
                consultas_comuns.append(consulta)

        lista_consultas_ordenada.extend(consultas_preferenciais)
        for i, consulta_preferencial in enumerate(consultas_comuns):
            index = (i + 1) * 1 + i 
            lista_consultas_ordenada.insert(index, consulta_preferencial)

        return lista_consultas_ordenada


class ComentarioCreate(CreateView):
    login_url = reverse_lazy('login')
    model = Comentario
    fields = ['sugestoes', 'nota']
    template_name = 'form.html'
    success_url = reverse_lazy('Listar-comentario')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['Titulo'] = 'Deixe sua sugestão'
        context['conteudo'] = 'Dê uma nota de 0 a 100'
        return context


class ComentarioList(ListView):
    model = Comentario
    template_name = 'listas/comentario.html'
    paginate_by = 5

