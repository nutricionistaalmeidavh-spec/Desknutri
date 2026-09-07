from __future__ import annotations

from datetime import datetime

LABELS = {
    'peso': 'Peso (kg)',
    'imc': 'IMC',
    'pg_final': 'Gordura (%)',
    'massa_magra': 'Massa magra (kg)',
    'cintura': 'Cintura (cm)',
}


def _value(row, key):
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def _dates(rows):
    out = []
    for r in rows:
        raw = _value(r, 'data')
        try:
            out.append(datetime.fromisoformat(raw))
        except (TypeError, ValueError):
            out.append(datetime.strptime(raw, '%d/%m/%Y'))
    return out


def _date_labels(rows):
    labels = []
    for dt in _dates(rows):
        labels.append(dt.strftime('%d/%m/%Y'))
    return labels


def patient_metric_figure(assessments, metric='peso'):
    """Gráfico longitudinal legado, mantido para compatibilidade."""
    import matplotlib.figure

    rows = [r for r in assessments if _value(r, metric) is not None]
    fig = matplotlib.figure.Figure(figsize=(7, 4), tight_layout=True)
    ax = fig.add_subplot(111)
    if rows:
        ax.plot(_dates(rows), [_value(r, metric) for r in rows], marker='o')
        ax.set_ylabel(LABELS.get(metric, metric))
    ax.set_title(f"Evolução — {LABELS.get(metric, metric)}")
    ax.grid(True, alpha=.2)
    return fig


def patient_evolution_figure(assessments):
    return patient_metric_figure(assessments, 'peso')


def _composition_values(row):
    weight = _value(row, 'peso')
    lean = _value(row, 'massa_magra')
    fat = _value(row, 'massa_gorda')
    pct = _value(row, 'pg_final')

    if fat is None and weight is not None and pct is not None:
        fat = weight * pct / 100.0
    if lean is None and weight is not None and fat is not None:
        lean = weight - fat
    if weight is None and lean is not None and fat is not None:
        weight = lean + fat
    if fat is None and weight is not None and lean is not None:
        fat = max(0.0, weight - lean)
    return weight, lean, fat


def patient_composition_figure(
    assessments,
    *,
    lean_color='#9A7895',
    fat_color='#F3C35B',
    total_color='#263746',
):
    """Comparação corporal aprovada: barras empilhadas + peso corporal total.

    Não altera nenhum cálculo clínico: usa massa magra/massa gorda persistidas e
    apenas deriva um componente quando ele está ausente e peso/% gordura existem.
    """
    import matplotlib.figure

    rows = []
    values = []
    for row in assessments:
        weight, lean, fat = _composition_values(row)
        if lean is None or fat is None:
            continue
        rows.append(row)
        values.append((weight if weight is not None else lean + fat, lean, fat))

    fig = matplotlib.figure.Figure(figsize=(8, 4.4), tight_layout=True)
    ax = fig.add_subplot(111)
    if not rows:
        ax.text(.5, .5, 'Sem dados de composição corporal', ha='center', va='center', transform=ax.transAxes)
        ax.set_axis_off()
        return fig

    x = list(range(len(rows)))
    totals = [v[0] for v in values]
    lean = [v[1] for v in values]
    fat = [v[2] for v in values]
    width = .46

    lean_bars = ax.bar(x, lean, width=width, color=lean_color, label='Massa livre de gordura (kg)', zorder=2)
    fat_bars = ax.bar(x, fat, width=width, bottom=lean, color=fat_color, label='Massa gorda (kg)', zorder=2)
    total_line, = ax.plot(x, totals, color=total_color, marker='o', linewidth=1.8, label='Peso corporal total (kg)', zorder=3)

    for bar, value in zip(lean_bars, lean):
        if value is not None:
            ax.text(bar.get_x() + bar.get_width()/2, value/2, f'{value:.1f}', ha='center', va='center', fontsize=8, color='white', fontweight='bold')
    for bar, base, value in zip(fat_bars, lean, fat):
        if value is not None:
            ax.text(bar.get_x() + bar.get_width()/2, base + value/2, f'{value:.1f}', ha='center', va='center', fontsize=8, color='#5E4721', fontweight='bold')
    for pos, total in zip(x, totals):
        ax.annotate(f'{total:.1f}', (pos, total), xytext=(0, 8), textcoords='offset points', ha='center', fontsize=8, color=total_color, fontweight='bold')

    ax.set_title('Composição corporal (kg)', loc='left', fontsize=11, fontweight='bold')
    ax.set_ylabel('kg')
    ax.set_xticks(x, _date_labels(rows))
    ax.grid(axis='y', alpha=.18, zorder=0)
    ax.legend(handles=[lean_bars, fat_bars, total_line], loc='upper center', bbox_to_anchor=(.5, 1.02), ncol=3, frameon=False, fontsize=8)
    return fig


def patient_weight_bmi_figure(assessments, *, weight_color='#A84770', bmi_color='#D7A9BC'):
    import matplotlib.figure

    rows = [r for r in assessments if _value(r, 'peso') is not None or _value(r, 'imc') is not None]
    fig = matplotlib.figure.Figure(figsize=(8, 4.2), tight_layout=True)
    ax = fig.add_subplot(111)
    if not rows:
        ax.text(.5, .5, 'Sem dados de peso e IMC', ha='center', va='center', transform=ax.transAxes)
        ax.set_axis_off()
        return fig

    x = list(range(len(rows)))
    weights = [_value(r, 'peso') or 0 for r in rows]
    bmis = [_value(r, 'imc') or 0 for r in rows]
    width = .34
    weight_bars = ax.bar([v - width/2 for v in x], weights, width=width, color=weight_color, label='Peso (kg)')
    ax2 = ax.twinx()
    bmi_bars = ax2.bar([v + width/2 for v in x], bmis, width=width, color=bmi_color, label='IMC')
    ax.set_ylabel('Peso (kg)')
    ax2.set_ylabel('IMC')
    ax.set_xticks(x, _date_labels(rows))
    ax.grid(axis='y', alpha=.18)
    ax.legend([weight_bars, bmi_bars], ['Peso (kg)', 'IMC'], loc='upper center', ncol=2, frameon=False, fontsize=8)
    ax.set_title('Peso e IMC', loc='left', fontsize=11, fontweight='bold')
    return fig


def patient_circumference_figure(assessments, *, waist_color='#A84770', hip_color='#D7A9BC'):
    import matplotlib.figure

    rows = [r for r in assessments if _value(r, 'cintura') is not None or _value(r, 'quadril') is not None]
    fig = matplotlib.figure.Figure(figsize=(8, 4.2), tight_layout=True)
    ax = fig.add_subplot(111)
    if not rows:
        ax.text(.5, .5, 'Sem circunferências registradas', ha='center', va='center', transform=ax.transAxes)
        ax.set_axis_off()
        return fig

    x = list(range(len(rows)))
    width = .34
    waist = [_value(r, 'cintura') or 0 for r in rows]
    hip = [_value(r, 'quadril') or 0 for r in rows]
    ax.bar([v - width/2 for v in x], waist, width=width, color=waist_color, label='Cintura (cm)')
    if any(hip):
        ax.bar([v + width/2 for v in x], hip, width=width, color=hip_color, label='Quadril (cm)')
    ax.set_ylabel('cm')
    ax.set_xticks(x, _date_labels(rows))
    ax.grid(axis='y', alpha=.18)
    ax.legend(loc='upper center', ncol=2, frameon=False, fontsize=8)
    ax.set_title('Circunferências', loc='left', fontsize=11, fontweight='bold')
    return fig


def patient_bodyfat_figure(assessments, *, color='#A84770'):
    import matplotlib.figure

    rows = [r for r in assessments if _value(r, 'pg_final') is not None]
    fig = matplotlib.figure.Figure(figsize=(8, 4.2), tight_layout=True)
    ax = fig.add_subplot(111)
    if not rows:
        ax.text(.5, .5, 'Sem percentual de gordura registrado', ha='center', va='center', transform=ax.transAxes)
        ax.set_axis_off()
        return fig
    x = list(range(len(rows)))
    values = [_value(r, 'pg_final') for r in rows]
    bars = ax.bar(x, values, width=.48, color=color)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, value, f'{value:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')
    ax.set_ylabel('%')
    ax.set_xticks(x, _date_labels(rows))
    ax.grid(axis='y', alpha=.18)
    ax.set_title('% Gordura', loc='left', fontsize=11, fontweight='bold')
    return fig


def growth_z_figure(measurements):
    import matplotlib.figure

    fig = matplotlib.figure.Figure(figsize=(7, 4), tight_layout=True)
    ax = fig.add_subplot(111)
    x = _dates(measurements)
    for key, label in [('waz', 'Peso/idade'), ('haz', 'Estatura/idade'), ('bmiz', 'IMC/idade')]:
        ys = [_value(r, key) for r in measurements]
        if any(v is not None for v in ys):
            ax.plot(x, ys, marker='o', label=label)
    for z in (-3, -2, 0, 1, 2, 3):
        ax.axhline(z, linewidth=.6, alpha=.25)
    ax.set_ylabel('Z-score WHO')
    ax.set_ylim(-4, 4)
    ax.legend()
    ax.grid(True, alpha=.2)
    return fig
