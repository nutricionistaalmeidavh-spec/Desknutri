# Matriz NutriDesk v6

| Entrega | Estado | Implementação |
|---|---|---|
| Exames laboratoriais estruturados | Implementado | `LabRepository`, `services/labs.py`, `LabsDialog` |
| Tendência por marcador | Implementado | `marker_series()` |
| Comparação longitudinal | Implementado | `services/longitudinal.py` + prontuário |
| Plano alimentar não enviado | Mantido/expandido | integrado às pendências inteligentes |
| Retorno não agendado | Implementado | regra derivada de consultas |
| Avaliação desatualizada | Implementado | regra padrão de 90 dias |
| Exame aguardando revisão | Implementado | `needs_review/reviewed_at` |
| Pendência manual | Implementado | `manual_pending_actions` |
| WhatsApp de saída | Implementado | plano, retorno, exame e follow-up |
| Importar pacientes CSV/XLSX | Implementado | prévia + duplicidade + histórico |
| Importar avaliações CSV/XLSX | Implementado | resolução de paciente e timeline |
| Importar exames CSV/XLSX | Implementado | painéis e marcadores |
| Pack Materno-infantil | Implementado | dados estruturados e ganho gestacional |
| Pack Esportiva | Implementado | treino, estratégias e hidratação |
| Pack Metabólica | Implementado | condições/metas/barreiras |
| Pack Renal | Implementado | metas e contexto renal |
| Pack Bariátrica | Implementado | fases, suplementos e sintomas |
| Pack Gastrointestinal | Implementado | Bristol/FODMAP/sintomas |
| Pack SIBO | Implementado | registro longitudinal não diagnóstico |
| Templates visuais | Implementado | 4 estilos iniciais |
| Template padrão por tipo | Implementado | Plano/Relatório/Orientação/Receita |
| PDF de plano estilizado | Implementado | refeições, totais, receitas e substituições |
| Substituições persistidas | Implementado | tabela `plano_substituicoes` |
| Substituições preservadas em revisão | Implementado | mapeamento item antigo → novo |
| Receitas enriquecidas | Implementado | categoria, tags, porções, modo de preparo |
| Relatório com exames | Implementado | seção opcional |
| Relatório com packs clínicos | Implementado | seção opcional |
| Menu principal sem especialidades isoladas | Implementado | packs ficam no prontuário |
| Diagnóstico automático de SIBO | Fora de escopo | propositalmente não implementado |
