# Документация Fury Linux

Основной вход для этого форка — **[состояние, эксплуатация и передача проекта](22-linux-handoff.md)**.
Документация сверена 30.10.2026; последние runtime-прогоны — 16.10.2026.
Форк остаётся на Fury0.4.5; обнаруженные новые upstream commits не интегрированы.

| Задача | Документ |
|---|---|
| Версии, изменения, hashes, данные, QA, ограничения и дальнейшие действия | [Linux handoff](22-linux-handoff.md) |
| Собрать и установить desktop/core | [Linux port](20-linux-port.md) |
| Понять, что взято из upstream issues/PR | [Review 16.10.2026](21-upstream-linux-review.md) |
| Проверить локальный relay, TLS и proxy behavior | [Прокси и сеть](05-proxy-networking.md) |
| Продолжить работу по критериям готовности | [План](09-roadmap.md) |
| Запустить проверки патчей на браузере | [core/verify](../core/verify/README.md) |

## Архитектура и справочники upstream

Ниже документы исходного проекта. Их Windows/macOS примеры, исторические
результаты и roadmap не означают, что те же ветки проверены в Linux-форке.
Linux status и границы измерений уточняются в документах20–22.

- [01 — Архитектура](01-architecture.md)
- [02 — Поверхность отпечатка](02-fingerprint-surface.md)
- [03 — Форк Chromium: сборка, патчи, ребейз](03-chromium-fork.md)
- [04 — Модель данных и права доступа](04-data-model-rbac.md)
- [05 — Прокси и сеть](05-proxy-networking.md)
- [06 — Синхронизация профилей](06-profile-sync.md)
- [07 — Базовая линия детектируемости](07-detection-baseline.md)
- [08 — Конкуренты и позиционирование](08-competitors.md)
- [09 — План работ](09-roadmap.md)
- [10 — Лицензии, право, ограничения](10-legal-licensing.md)
- [11 — Что стоит денег, а что нет](11-budget.md)
- [12 — UX-референс: разбор AdsPower](12-ui-reference.md)
- [13 — Свой сервер](13-self-hosting.md)
- [Сервер для команды: от пустой машины до выданных доступов](14-team-server.md)
- [Installing Fury](15-install.md)
- [15 — Установка](15-install.ru.md)
- [16 — Паритет и то, что дальше](16-parity-and-beyond.md)
- [17 — Apple Developer: как получить подпись](17-apple-signing.md)
- [18. Android-персоны на десктопном ядре](18-android.md)
- [Using Fury](19-guide.md)
- [Как пользоваться Fury](19-guide.ru.md)
