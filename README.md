# fdi-sbc-2504
## Sistema Basado en Conocimiento - Dominio Culinario

Sistema experto desarrollado para **Sistemas Basados en Conocimiento (SBC) 2025/26**. Implementa un motor de inferencia que trabaja con bases de conocimiento representadas mediante tripletas (sujeto, predicado, objeto).

### Miembros del Equipo

- Carmen Granados
- Vega García
- Marcos Poza
- Daniel Higueras

### Dominio de Conocimiento

**Dominio culinario**: gestión de ingredientes, recetas, maridajes y disponibilidad en despensa.

#### Ejemplos de conocimiento
- Propiedades de ingredientes: `tomate cantidad muchos`, `manzana sabor acido`
- Maridajes: `vino tinto marida carne`
- Reglas de inferencia: `receta disponible gazpacho <- tomate disponible despensa`

### Uso

```bash
# Iniciar el sistema
uv run -m sbc.cli

# Comandos principales
"""TODO: por completar"""
```

### Estructura

```
fdi-sbc-2504/
├── sbc/
│   ├── clases.py     # Tripleta y Sustitucion
│   ├── cli.py        # Interfaz CLI
│   └── motor.py      # Motor de inferencia
├── kb/
│   └── bc.txt        # Base de conocimiento
└── doc/
    └── doc-bc.txt    # Documentación
```
---

**Curso**: Sistemas Basados en Conocimiento 2025/26