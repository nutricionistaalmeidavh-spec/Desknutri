"""Single, atomic clinical-consultation workflow.

Appointment identity, progress and plan provenance are committed together.
No network, SaaS service or paid dependency is required.
"""
from __future__ import annotations

from datetime import date, datetime, time
from uuid import uuid4

from nutridesktop.data.database import Database, db


def _required_time(value):
    parsed = time.fromisoformat(value)
    if parsed.second or parsed.microsecond:
        raise ValueError("Informe o horário no formato HH:MM.")
    return parsed.strftime("%H:%M")


def complete_guided_consultation(
    *, database: Database = db, patient_id: int, date_value: str, time_value: str,
    kind: str = "Consulta", objective: str = "", approach: str = "", notes: str = "",
    anamnesis: str = "", appointment_id: int | None = None,
    idempotency_key: str | None = None, plan_id: int | None = None,
    plan_delivered: bool = False, return_date: str | None = None,
    return_time: str | None = None, request_reassessment: bool = False,
    request_plan_update: bool = False,
) -> int:
    """Finish exactly one consultation; error or retry never leaves partial records.

    A scheduled appointment is completed in place. For standalone consults,
    a same-patient/date/time scheduled record is reused automatically.
    A stable UI-provided idempotency key protects retry after a lost response.
    """
    date.fromisoformat(date_value)
    hour = _required_time(time_value)
    if return_date:
        date.fromisoformat(return_date)
        if return_date < date_value:
            raise ValueError("Retorno não pode ser anterior à consulta.")
        return_time = _required_time(return_time or "")
    if plan_delivered and plan_id is None:
        raise ValueError("Selecione o plano efetivamente entregue para confirmar o envio.")
    if not kind.strip():
        raise ValueError("Informe o tipo de consulta.")

    key = idempotency_key or str(uuid4())
    with database.transaction() as c:
        if not c.execute("SELECT id FROM pacientes WHERE id=?", (patient_id,)).fetchone():
            raise ValueError("Paciente não localizado.")
        retry = c.execute("SELECT id FROM consultas WHERE finalization_key=?", (key,)).fetchone()
        if retry:
            return retry["id"]

        plan_version = None
        if plan_delivered:
            selected = c.execute(
                "SELECT paciente_id,version_no,status FROM planos WHERE id=?", (plan_id,)
            ).fetchone()
            if (not selected or selected["paciente_id"] != patient_id
                    or selected["status"] != "Ativo"):
                raise ValueError("Escolha uma versão ativa do plano deste paciente.")
            plan_version = selected["version_no"]

        appointment = None
        if appointment_id is not None:
            appointment = c.execute(
                "SELECT * FROM consultas WHERE id=? AND paciente_id=?",
                (appointment_id, patient_id),
            ).fetchone()
            if not appointment:
                raise ValueError("Agendamento selecionado não pertence ao paciente.")
            if appointment["status"] not in ("Agendada", "Remarcada"):
                raise ValueError("O agendamento já foi concluído ou não está disponível.")
        else:
            candidates = c.execute(
                """SELECT * FROM consultas WHERE paciente_id=? AND data=? AND hora=?
                   AND status IN ('Agendada','Remarcada')""",
                (patient_id, date_value, hour),
            ).fetchall()
            if len(candidates) > 1:
                raise ValueError("Há agendamentos duplicados neste horário. Selecione um deles.")
            if candidates:
                appointment = candidates[0]
            elif c.execute(
                """SELECT 1 FROM consultas WHERE paciente_id=? AND data=? AND hora=?
                   AND status='Realizada'""",
                (patient_id, date_value, hour),
            ).fetchone():
                raise ValueError("Já existe consulta realizada neste horário para este paciente.")

        completed_at = datetime.now().isoformat(timespec="seconds")
        if appointment:
            consultation_id = appointment["id"]
            c.execute(
                """UPDATE consultas SET data=?,hora=?,tipo=?,status='Realizada',
                   objetivo=?,abordagem=?,observacoes=?,finalizada_em=?,finalization_key=?,
                   plano_enviado_em=?,plano_id_enviado=?,plano_versao_enviada=?,
                   reassessment_requested=?,plan_update_requested=? WHERE id=?""",
                (date_value, hour, kind, objective, approach, notes, completed_at, key,
                 completed_at if plan_delivered else None, plan_id if plan_delivered else None,
                 plan_version, int(request_reassessment), int(request_plan_update), consultation_id),
            )
        else:
            consultation_id = c.execute(
                """INSERT INTO consultas(
                   paciente_id,data,hora,tipo,status,objetivo,abordagem,observacoes,
                   finalizada_em,finalization_key,plano_enviado_em,plano_id_enviado,
                   plano_versao_enviada,reassessment_requested,plan_update_requested)
                   VALUES(?,?,?,?,'Realizada',?,?,?,?,?,?,?,?,?,?)""",
                (patient_id, date_value, hour, kind, objective, approach, notes,
                 completed_at, key, completed_at if plan_delivered else None,
                 plan_id if plan_delivered else None, plan_version,
                 int(request_reassessment), int(request_plan_update)),
            ).lastrowid

        if anamnesis.strip():
            import json
            data = {"Consulta": anamnesis.strip(), "Objetivo": objective, "Orientações": notes}
            version = c.execute(
                "SELECT COALESCE(MAX(versao),0)+1 FROM anamneses_paciente WHERE paciente_id=?",
                (patient_id,),
            ).fetchone()[0]
            saved = c.execute(
                """INSERT INTO anamneses_paciente(
                   paciente_id,nome_modelo,conteudo,data,tipo,dados_json,versao)
                   VALUES(?,?,?,?,?,?,?)""",
                (patient_id, "Consulta guiada", "\n".join(
                    f"{k}: {v}" for k, v in data.items() if str(v).strip()
                ), date_value, "Consulta guiada", json.dumps(data, ensure_ascii=False), version),
            ).lastrowid
            c.execute(
                """INSERT INTO timeline_events(
                   paciente_id,event_type,event_date,title,entity_id)
                   VALUES(?,?,?,?,?)""",
                (patient_id, "anamnese", date_value, f"Anamnese v{version}", saved),
            )

        for required, kind_name, title in (
            (request_reassessment, "reassess_after_consultation", "Registrar reavaliação"),
            (request_plan_update, "plan_update_after_consultation", "Atualizar plano alimentar"),
        ):
            if required:
                c.execute(
                    """INSERT INTO manual_pending_actions(paciente_id,kind,title,detail,severity)
                       VALUES(?,?,?,?,'media')""",
                    (patient_id, kind_name, title,
                     f"Solicitado na consulta #{consultation_id}. Conclua no prontuário."),
                )

        if return_date:
            existing_return = c.execute(
                """SELECT id FROM consultas WHERE paciente_id=? AND retorno_de_id=?
                   AND data=? AND hora=? AND status NOT IN ('Cancelada','Faltou')
                   LIMIT 1""",
                (patient_id, consultation_id, return_date, return_time),
            ).fetchone()
            if not existing_return:
                c.execute(
                    """INSERT INTO consultas(
                       paciente_id,data,hora,tipo,status,retorno_de_id,duracao_min)
                       VALUES(?,?,?,'Retorno','Agendada',?,60)""",
                    (patient_id, return_date, return_time, consultation_id),
                )
        return consultation_id
