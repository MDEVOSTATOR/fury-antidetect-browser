# Fury Linux: состояние, эксплуатация и передача проекта

Документация обновлена **02.11.2026** после [исправления CSS system colours](23-css-system-colors.md).
Последние браузерные проверки выполнены 02.11.2026: новое ядро linux2, 53 утверждения
для Windows colours в X11/Wayland, Linux full probes и installed smoke.
Исторические полные прогоны 16.10 и read-only inventory 30.10 отмечены отдельно.

## Состояние и версии

| Позиция | Зафиксированное состояние |
|---|---|
| Публичный форк | [MDEVOSTATOR/fury-antidetect-browser](https://github.com/MDEVOSTATOR/fury-antidetect-browser) |
| Основная ветка форка | `port/linux-x64` |
| База | Fury 0.4.5, upstream `a8130657be78ac812d0b96d34003c19126da1a29` |
| Проверенный код Linux-порта | `331e8ff2624f717990098e965bf140911e222acd`; последующие документационные коммиты не означают пересборку |
| Chromium | 155.0.8059.39, source `3ff7ac5a9224be9156d7f8703a06e22890aafd34` |
| Серия патчей | 38: 36 upstream + Linux zygote0002 + CSS system colours0022 |
| Целевая система | Ubuntu 24.04 x86_64; GTK3 / WebKitGTK4.1 |
| Установленные пакеты | `fury 0.4.5`, `fury-core 0.4.5+linux2` |
| Проверенная графика | X11/Xvfb и native Wayland на Weston13 headless/Pixman; SwiftShader |
| Не подтверждено | Hardware GPU/WebGPU, интерактивные GNOME/KDE/Hyprland, другие дистрибутивы и Linux team-mode E2E |
| Доставка | Исходники опубликованы; на 02.11.2026 в GitHub Releases форка нет Linux-бинарников |

При fetch 30.10.2026 upstream main оказался на **33 коммита впереди**
относительно зафиксированной базы: версия 0.4.18, commit `2ac7a7ac5f15c2a5184914555a13c65e6094fc76`
от 28.10.2026. Эти изменения не интегрированы: документационная сверка
не является обновлением приложения. Исторический разбор issues от 16 октября
не следует читать как текущий статус всех upstream issues.

При fetch02.11.2026 upstream уже содержит0.4.20, commit `7b4fe8a167fdb0bd74331e836e888d0a83ce4973`;
не интегрированы40коммитов. CSS fix сделан поверх проверенной базы0.4.5.
В отдельный review входят и обновления зависимостей, в частности upstream
переход Rustls на0.23.46 (commit05c5d48); этот набор не переносился вместе с CSS.

## Карта документации

- [Сборка, установка и первоначальные измерения](20-linux-port.md).
- [Результаты проверки upstream issues и выборочные backports](21-upstream-linux-review.md).
- [Прокси, TLS и поведение релея](05-proxy-networking.md).
- [Архитектура приложения](01-architecture.md), [Chromium и патчи](03-chromium-fork.md).
- [Проверки реального браузера](../core/verify/README.md).
- [План Linux-форка и исторический план upstream](09-roadmap.md).
- [CSS system colours: воспроизведение, patch и runtime A/B](23-css-system-colors.md).
- [Общий указатель](README.md).

## Устройство и важные файлы

| Компонент | Роль и реализация |
|---|---|
| Desktop | Tauri/React; Linux-specific package config: [tauri.linux.conf.json](../desktop/src-tauri/tauri.linux.conf.json) |
| Агент | Профили, локальная SQLite, IPC, запуск ядра и relay: [agent/src](../agent/src) |
| Пути и IPC | Общие функции для GUI и агента: [dirs.rs](../platform-rs/src/dirs.rs), [ipc.rs](../platform-rs/src/ipc.rs) |
| Персоны | Linux capture/schema/consistency checks: [shared-rs/src](../shared-rs/src), [persona.schema.json](../shared/persona.schema.json) |
| Запуск Chromium | [launcher.rs](../agent/src/launcher.rs): shared config, relay, CDM staging, Ozone selection |
| TLS к прокси | [relay.rs](../agent/src/relay.rs), parser в [main.rs](../agent/src/main.rs), ошибки в [diagnose.rs](../agent/src/diagnose.rs) |
| Widevine | [widevine.rs](../agent/src/widevine.rs): копирование из установленного Chrome в приватный профиль |
| Linux build | [core/args/linux-x64.gn](../core/args/linux-x64.gn), [tools/linux](../tools/linux) |
| Runtime проверки | [verify-core.mjs](../tools/linux/verify-core.mjs), [verify-agent.py](../tools/linux/verify-agent.py), [core/verify](../core/verify) |

Обычный путь трафика: браузер → локальный HTTP/CONNECT relay → upstream proxy.
Доступ к HTTPS-сайту через HTTP-прокси и TLS-соединение с HTTPS-прокси — две
разные проверки; обе выполнены. У HTTPS-прокси CONNECT и Proxy-Authorization
передаются после проверки TLS-сертификата самого прокси.

## Что было сделано

| Этап | Результат |
|---|---|
| Начальный порт, `0718f3e` | Linux desktop/agent/core build tooling, Debian packaging, Linux capture и пути |
| Согласование runtime, `f20530c` | Точная зависимость оболочки от версии core-пакета |
| Zygote, `79b2e76` | Config читается после Linux fork до создания thread pool; раньше дочерние процессы могли остаться без настроек |
| Schema/keyring, `2cb2c9d` / `8ca4f2e` | Linux-формат capture, актуальные поля схемы, объяснение Secret Service |
| Первая валидация, `a19f760` | Собран и установлен Chromium155 с 37 патчами, сохранены результаты |
| Переносимые тесты, `87e3cb6` | Выбор доступных шрифтов, учёт classic scrollbar, Linux executable branding |
| Выборочные backports, `6a0fdf7` | Native Wayland/X11 selection и проверенный TLS к HTTPS-прокси из PR10 |
| CSS colours, `331e8ff` | Windows light palette, renderer Highlight,53 assertions; package revision2 и isolated candidate output |

Отдельно исправлены ложные срабатывания detect-suite: cross-context control
использует одинаковый ASCII/Arial, основной Unicode Canvas fingerprint сохранён.
Убран ServiceWorker bypass и исправлен no-port reply генератора.
Контроль обычным Chrome прошёл базовую согласованность и ожидаемо провалил
различие Canvas между seed: стенд различает patched и stock поведение.

Полный upstream PR10 не сливался. Server/RBAC/transfer/UI/AppImage-части
и C++-эксперимент PR13 не входят в этот проверенный набор.
[Подробная матрица решений](21-upstream-linux-review.md).

## Сборка и повторная установка

Все команды ниже выполняются из корня репозитория. Зависимости и полный порядок —
в [инструкции сборки](20-linux-port.md#сборка).

```sh
git clone --branch port/linux-x64 https://github.com/MDEVOSTATOR/fury-antidetect-browser.git
cd fury-antidetect-browser
source tools/linux/env.sh
tools/linux/build-shell.sh
J=8 tools/linux/build-core.sh
tools/linux/status.sh
```

`env.sh` подключает project-local Rust при наличии, выбирает настоящий GCC
вместо пользовательского wrapper с именем cc и снимает унаследованный
realtime scheduling у текущего процесса. По умолчанию Cargo jobs=6,
core jobs=8; sync ограничен четырьмя jobs. Full core build занимает часы,
incremental output нужно сохранять. Изменение patch checksum требует
явного согласования source tree; script не сбрасывает чужие изменения.

Изменения только агента/GUI требуют пересборки shell-пакета. Изменение C++,
Chromium revision или patch series требует пересборки и проверки core;
успешная упаковка сама по себе не подтверждает работу браузера.

```sh
(cd dist-linux && sha256sum -c SHA256SUMS-shell)
(cd dist-linux && sha256sum -c fury-core_0.4.5+linux2_amd64.deb.sha256)
tools/linux/install.sh
fury-desktop
```

Installer вызывает apt --reinstall с обычным подтверждением: exact core dependency
обновляется и при прежней upstream-версии desktop.
Linux revision задаётся в core/LINUX_PACKAGE_REVISION, Tauri dependency проверяется build-shell.
Новые пакеты можно складывать в отдельный output directory для QA перед установкой. Для заранее согласованной
неинтерактивной установки после проверки checksum использовался apt-get -y
с явными путями к обоим пакетам. Установленный helper должен быть root:root4755
в root-owned каталоге. Tar-архив предназначен для разработчика и сам по себе
не настраивает root-owned sandbox для Ubuntu24.

```sh
dpkg-query -W fury fury-core
dpkg -V fury fury-core
stat -c '%U:%G %a %n' /usr/lib/fury-core/chrome-sandbox
/usr/lib/fury-core/chrome --version
```

## Локальные артефакты

Сверены02.11.2026 с `dist-linux/BUILD-INFO.json`:

| Файл | Bytes | SHA256 |
|---|---:|---|
| `Fury_0.4.5_amd64.deb` | 13815294 | `ca619add08c472169aba6e1ca0a4256ae90d48ce42b50b31e1644c6a2bdec491` |
| `fury-core-0.4.5-linux-x64-r2.tar.xz` | 148807960 | `6cbea7d45f1b3f2225df6ebb426c4dbe66e2d30b3b48aa7302077724bb17985b` |
| `fury-core_0.4.5+linux2_amd64.deb` | 157714552 | `78269c81a844af86f8081841acc75b710dbe119b0281d0c3289c6d6cdb8e214f` |

SHA256 установленного `/usr/bin/fury-agent`:
`8567e2a5ec41cd4cd324b056639ff4bbb37a94ff0c812a8e1ffcfbee818fb311`.
Он совпадал с протестированным release-agent при установке 16 октября;
30 октября и2ноября повторно проверены пакетная целостность и текущее значение hash.

В пакетах сохранены LICENSE/NOTICE и сгенерированные Chromium credits.
Проприетарный Widevine CDM не распространяется в комплекте.
При новой сборке обновлять checksum-файлы и локальный BUILD-INFO:
эти значения относятся к конкретным байтам, а не ко всем будущим сборкам 0.4.5.

## Запуск, данные и настройки

Обычный запуск — `fury-desktop` или пункт Fury в меню. GUI и агент должны
разрешать один и тот же каталог данных.

| Настройка | Поведение |
|---|---|
| Без overrides | `$XDG_DATA_HOME/fury` либо `~/.local/share/fury` |
| `FURY_HOME` | Отдельный data root; внутри SQLite `fury.db`, профили, персоны, логи |
| `FURY_SOCKET` | Явный IPC endpoint; default — короткий temporary socket с tag от data root |
| `FURY_CORE` | Явный dev-core; не обычный способ обновить установленный runtime |
| Пакетное ядро | `/usr/lib/fury-core/chrome`; ищется до пользовательского core.bundle |
| `WAYLAND_DISPLAY` | При непустом значении агент выбирает `--ozone-platform=wayland` |
| `FURY_OZONE_PLATFORM=x11` | Явный совместимый X11/XWayland вариант; override важнее среды |
| Нет Wayland/override | Агент сохраняет стандартный выбор Chromium |

Выбор backend происходит до запуска; автоматического повторного запуска через
другой backend при ошибке нет. Изменения environment должен получить агент:
перезапуск только GUI может оставить ранее запущенный агент со старой средой.

Для обычной работы снимите свою Linux-персону в настройках через установленный
Google Chrome. Capture использует временный профиль. Upstream catalogue
Windows/macOS и локальная software QA-персона не заменяют снимок своей машины.

Для proxy secrets нужен доступный разблокированный Secret Service, например
GNOME Keyring. Без него сессию нельзя считать проверенным защищённым хранилищем.
Backup данных требует сохранности и data root, и ключевого материала/keyring;
копия SQLite сама по себе не гарантирует расшифровку proxy secrets.
Данные копируют согласованно, после закрытия нужных профилей и их агента.
QA не должен открывать или менять рабочие браузерные профили.

## Результаты проверок

У каждой группы указана дата; исторический полный набор не выдаётся за новый прогон.

| Уровень | Результат и границы |
|---|---|
| Первоначальные unit-тесты,16.10 | 415 PASS: agent229, shared114, platform20, detect13, desktop39 |
| После backport PR10,16.10 | `cargo test -p fury-agent`: 236 PASS / 0 FAIL; это отдельный поздний прогон изменённого crate |
| Расширенный C++/CDP | Первый прогон 25/33 PASS; после целевых исправлений и повторов 29 PASS, 4 не подтверждены |
| Не подтверждены | 0041 голоса, 0060 устройства, 0070 baseline ICE, 0121 батарея: отсутствуют нужные контрольные состояния |
| Не запускались | 0032 WebGPU, 0903 macOS, 0902 с намеренным no-sandbox control |
| DPR | 28/28 на явно виртуальном 2x display; это не физический HiDPI GPU |
| Gate X11 и Wayland,02.11 | По шесть новых captures на backend; в каждом12PASS/0FAIL/1WebGPUskip |
| CSS0022,02.11 | Старое ядро21/53FAIL; новое53/53PASS отдельноX11/nativeWayland; публичныйplatformMismatch0.5→-1 |
| Шифрование cookies | Нет plaintext на диске; тот же ключ читает, другой не читает; браузер остаётся работоспособным |
| Agent storage, повтор02.11 | Create/trash/restore, IPC0600, encrypted SQLite secrets и чтение после restart |
| HTTPS proxy | Доверенная CA: auth CONNECT и payload внутри TLS; чужая CA/hostname mismatch:502 до отправки credentials |
| Установленный GUI,16.10 | Запуск X11 и native Wayland, IPC с агентом, найдено пакетное ядро; screenshots проверены |
| Network smoke,16.10 | HTTPS example.com через HTTP relay; проверка сертификата сайта не отключалась |

Тест 0303 не достигает native bookmark export dialog; эту ветку проверенной
не считаем. Полный набор C++/CDP не объявляется зелёным.
GitHub CI не заменяет эти замеры: Chromium на hosted runner не собирается,
а push-trigger текущего workflow ограничен main, не port/linux-x64.

## Как повторять QA

Нужны отдельная Linux QA-персона, установленные пакеты, Node с WebSocket API,
Python3, Xvfb/dbus-run-session и GNOME Keyring. Для Widevine — установленный
Chrome с доступным CDM. Пример создаёт отдельные XDG-каталоги и keyring:

```bash
source tools/linux/env.sh
cargo build --release -p fury-detect
export FURY_QA_PERSONA=/absolute/path/to/linux-qa-persona.json
test -f "$FURY_QA_PERSONA"
FURY_QA_ROOT="$(mktemp -d /tmp/fury-qa.XXXXXX)"
export XDG_DATA_HOME="$FURY_QA_ROOT/data"
export XDG_CONFIG_HOME="$FURY_QA_ROOT/config"
export XDG_RUNTIME_DIR="$FURY_QA_ROOT/run"
export FURY_QA_OUT="$FURY_QA_ROOT/evidence"
mkdir -p "$XDG_DATA_HOME" "$XDG_CONFIG_HOME" "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
export FURY_QA_SOFTWARE_GPU=1 FURY_QA_REQUIRE_WIDEVINE=1
export FURY_OZONE_PLATFORM=x11 FURY_QA_OZONE_PLATFORM=x11
unset WAYLAND_DISPLAY CHROME_DEVEL_SANDBOX
xvfb-run -a -s '-screen 0 1600x900x24' dbus-run-session -- bash <<'QA'
set -euo pipefail
python3 -c 'import secrets; print(secrets.token_hex(16))' |
  gnome-keyring-daemon --unlock --components=secrets >/dev/null
python3 tools/linux/verify-agent.py /usr/bin/fury-agent --persona "$FURY_QA_PERSONA"
node tools/linux/verify-core.mjs /usr/lib/fury-core/chrome /usr/bin/fury-agent   "$FURY_QA_PERSONA" "$FURY_QA_OUT"
for capture in "$FURY_QA_OUT"/seed-*-run-*.json; do
  target/release/fury-detect gate "$capture"
done
QA
```

Software GPU и WebKit DMABUF flags использовались только в QA, не стали
production defaults. Для native Wayland нужен отдельный compositor и его
короткий private runtime socket; DISPLAY удаляется, FURY_OZONE_PLATFORM
снимается, FURY_QA_OZONE_PLATFORM=wayland проверяет actual command line.
При проверке screen0020 нативный display должен отличаться от целевых1920x1080.
Подробности отдельных assertions — в [core/verify](../core/verify).

## Локальные доказательства и восстановление стенда

| Путь от корня checkout | Содержимое |
|---|---|
| `.build/qa/fury-core-final/` | Первые packaged-core captures и sandbox status |
| `.build/qa/validation-20261016T185631Z/` | 33-сценарный прогон, targeted reruns, JSON summary, GUI screenshot |
| `.build/upstream-review/` | Snapshot issues/PR/comments/diffs, unit/release/package/install logs и CLI TLS smoke helper |
| `.build/upstream-review/runtime-20261016T192133Z/` | Native Wayland/X11 captures, gate logs, установленный GUI и screenshot |
| `.build/link-colors-review/` | CSS before/after,53 assertions, new Linux probes, installed detector, rollback packages |
| `.build/documentation-audit-20261030.json` | Исторический read-only inventory 30.10.2026 |
| `dist-linux/BUILD-INFO.json` | Source 331e8ff, 38 patches, linux2, historical unit dates and fresh CSS/browser validation metadata |
| `.build/linux-core.phase` | `validated-installed`; историческая отметка, не процесс мониторинга runtime |

Эти пути игнорируются Git и не приезжают с clone. Исторические helper scripts
в .build не являются установленным API. Долговечные регрессионные тесты находятся
в исходниках. Перед очисткой build/QA data сохраняют нужные evidence и артефакты.

На исходной машине `core/src` — symlink на `/home/fury-linux-build-20261016/src`;
output — `out/linux-x64.noindex` внутри этого tree. Это позволяет продолжать
incremental build. Перемещение туда устранило захват постороннего
node_modules из родительского каталога; на другой машине нужен собственный
чистый путь исходников. Ранее временные reference/runtime copies из
/opt/fury-linux-qa перенесены в `.build/qa/retired-runtime/` со снятым setuid.
Рабочий sandbox helper остаётся только в пакетной root-owned установке.

## Известные трудности и порядок действий

| Симптом | Проверка и действие |
|---|---|
| Не работает WebGL под Xvfb | Проверить renderer; software QA включается явно, hardware coverage этим не появляется |
| Root helper/AppArmor error | Проверить пакетную установку и root:root4755; не отключать AppArmor/sysctl и не setuid helper в writable source tree |
| Core package не найден | Собрать/передать оба .deb; upstream updater не поставляет Linux runtime нашего форка |
| Secret Service недоступен | Проверить свою DBus-сессию и keyring; headless session без vault не считается успешной |
| GTK/IPC не стартует в глубоком QA-path | Проверить длину AF_UNIX socket; использовать короткий private /tmp runtime |
| TLS fixture отвергнут CaUsedAsEndEntity | Отдельная CA и leaf с CA:false; validation не ослаблять |
| Chromium TSGo тянет чужой buffer | Проверить node_modules среди предков source path, сохранить incremental output при переносе |
| После смены backend всё по-старому | Проверить environment уже запущенного агента, а не только GUI |
| Полный verify suite вернул nonzero | Разобрать control/assertion; отсутствие голоса/батареи/ICE нельзя переименовать в PASS |

## Оставшаяся работа и границы выводов

Порядок: review 33 новых upstream commits → согласование source/core pins и
patch series → тестовая сборка → changed-crate и браузерные тесты → установка
и повторный smoke → публикация. Не подменять version stamp или core обычным Chrome.

Отдельно остаются hardware GPU/WebGPU, реальные Wayland desktop sessions,
полноценные font local()/NetworkInformation проверки перед PR13, Linux team E2E,
hosted CI для Linux-ветки и выпуск публичных Linux-binaries с checksums/source pin.
Это план работ, не выполненные пункты.

Широкое сравнение с Dolphin Anty не подтверждено A/B-прогоном двух браузеров.
Начальный source audit и работа Linux-порта не доказывают превосходство над
конкурентом. В background logs свежего Chromium наблюдались попытки запросов к
Google, блокированные закрытым QA-upstream; содержимое не исследовалось.
Не выводить нулевую сетевую активность из формулировки upstream «no telemetry».
