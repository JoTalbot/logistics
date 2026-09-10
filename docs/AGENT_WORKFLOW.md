# Distributed Agent Workflow

Этот документ описывает практический цикл каждого AI-агента в `JoTalbot/logistics`.

## Перед началом

```text
1. Read AGENTS.md
2. Read STATUS.md
3. Inspect repository and recent commits
4. Identify current project step
5. Identify available work areas
6. Check local/project/installed skills
7. Search GitHub for existing implementations
8. Deep-search the current internet
9. Check official documentation/API references
10. Claim a non-conflicting work area
11. Write current task into STATUS.md
```

## Перед каждым существенным шагом

Повторять research gate, даже если предыдущий шаг уже исследовался. Причина: API, документация, репозитории, skills и состояние проекта могут измениться между шагами.

```text
CURRENT STATE
   ↓
PROJECT SEARCH
   ↓
SKILL SEARCH
   ↓
WEB RESEARCH
   ↓
GITHUB RESEARCH
   ↓
OFFICIAL DOCS
   ↓
DESIGN DECISION
   ↓
IMPLEMENT
   ↓
VERIFY
   ↓
UPDATE STATUS
   ↓
LOG
   ↓
EXTRACT LESSONS
   ↓
UPDATE AGENT SKILL
   ↓
COMMIT
```

## Research record

Для каждого существенного шага в agent log сохранять:

```text
STEP:
QUESTION:
PROJECT_FINDINGS:
SKILLS_CHECKED:
WEB_SOURCES:
GITHUB_REPOS:
OFFICIAL_DOCS:
DECISION:
WHY:
RISKS:
IMPLEMENTATION:
VERIFICATION:
NEXT:
```

## Parallel safety

Не делать предположений о локальном checkout другого агента. Общая истина находится в GitHub. Перед изменением общего файла повторно проверить его актуальную версию.

Если две задачи можно выполнить независимо, они должны выполняться параллельно в отдельных областях/ветках/коммитах.

Если изменения конфликтуют, сначала синхронизироваться с текущим состоянием `main`/PR и выбрать минимальную безопасную область изменения.

## Skill evolution

Agent log является сырьём. После завершения задачи агент извлекает из него повторяемые знания и обновляет `docs/agent-skills/<agent-id>.md`.

Skill не должен содержать:
- секреты;
- токены;
- пароли;
- лишние персональные данные;
- бессмысленную полную транскрипцию.

Skill должен содержать проверенные процедуры и lessons learned.

## Handoff

Каждый агент завершает работу записью в `STATUS.md` и собственном логе:

```text
DONE:
VERIFIED:
RESEARCHED:
FILES:
COMMITS:
OPEN_ISSUES:
NEXT_STEP:
```

Следующий агент начинает с чтения этих данных.
