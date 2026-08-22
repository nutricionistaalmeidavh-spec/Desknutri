from __future__ import annotations
import re
from urllib.parse import quote


def normalize_br_phone(phone):
    digits=re.sub(r'\D','',str(phone or ''))
    if not digits:raise ValueError('Paciente sem telefone válido.')
    if digits.startswith('55'):
        normalized=digits
    else:
        normalized='55'+digits
    if len(normalized)<12 or len(normalized)>13:raise ValueError('Telefone inválido para WhatsApp.')
    return normalized


def build_whatsapp_url(phone,message):
    return f"https://wa.me/{normalize_br_phone(phone)}?text={quote(str(message or ''),safe='')}"


def message_for(kind,patient_name,context=None):
    context=context or {};name=str(patient_name or '').strip() or 'Olá'
    presets={
        'plan':f"Olá, {name}! Seu plano alimentar está pronto. Se precisar de alguma orientação sobre o material, me avise por aqui.",
        'return':f"Olá, {name}! Passando para lembrar do seu retorno nutricional. Se precisar ajustar o horário, me avise.",
        'exam':f"Olá, {name}! Para seguirmos com seu acompanhamento, quando puder envie os exames/resultados combinados na consulta.",
        'followup':f"Olá, {name}! Como você está evoluindo desde nossa última consulta? Se tiver alguma dificuldade importante com o plano, me conte.",
    }
    msg=presets.get(kind,presets['followup'])
    if context.get('date') and kind=='plan':msg+=f" Referência: {context['date']}."
    return msg
