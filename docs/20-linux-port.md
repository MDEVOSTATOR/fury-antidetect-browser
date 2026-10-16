# Linux x86_64 port

Публичный форк: [MDEVOSTATOR/fury-antidetect-browser](https://github.com/MDEVOSTATOR/fury-antidetect-browser).
Основная ветка форка — Linux-адаптация. В GitHub опубликованы исходники;
готовые Linux-пакеты в Releases ещё не загружены. Перечисленные ниже артефакты
создаются локальной сборкой.

Рабочая ветка: `port/linux-x64`, база Fury 0.4.5 (`a813065`). Целевая система
для первой сборки: Ubuntu 24.04 x86_64, GTK 3 / WebKitGTK 4.1. Поддержку других
дистрибутивов и интерактивных Wayland-десктопов нужно проверять отдельно.

Приложение и ядро собраны и установлены. Запуск: меню приложений **Fury** либо
`fury-desktop`. Установленные пакеты: `fury 0.4.5` и `fury-core 0.4.5+linux1`.
Проверены X11/Xvfb, браузер и запуск интерфейса на отдельном native Wayland compositor
Weston/Pixman со SwiftShader. Аппаратный GPU и интерактивные GNOME/KDE/Hyprland
сессии отдельно не проверялись. [Разбор upstream и новые проверки](21-upstream-linux-review.md).

Комплект в `dist-linux/`:

- `Fury_0.4.5_amd64.deb` — оболочка и агент;
- `fury-core_0.4.5+linux1_amd64.deb` — Chromium с патчами и sandbox helper;
- `.sha256` / `SHA256SUMS-shell` — контрольные суммы;
- `fury-core-0.4.5-linux-x64.tar.xz` — архив runtime для разработчиков.

Для Ubuntu рекомендуется установка двух `.deb` через `tools/linux/install.sh`.

## Сборка

Rust можно установить локально в `.build/cargo` / `.build/rustup`, не меняя
профиль пользователя. `tools/linux/env.sh` подключает эту установку, если она есть,
и явно выбирает системный C-компилятор. На машине разработки `cc` оказался
пользовательской командой управления сессиями; использовать его как linker нельзя.
Окружение сборки сбрасывает унаследованный realtime scheduler на обычный;
Chromium компилируется с nice 10 и ограничением числа jobs. Это касается только
процессов текущей сборки, настройки других проектов не меняются.

Зависимости оболочки на Ubuntu:

```sh
sudo apt-get install --no-install-recommends build-essential pkg-config \
  libwebkit2gtk-4.1-dev libxdo-dev libssl-dev \
  libayatana-appindicator3-dev librsvg2-dev libsecret-1-dev ninja-build
sudo apt-get install --no-install-recommends python3-pil
tools/linux/build-shell.sh
```

Оболочка собирается в `.deb`, агент поставляется как sidecar. Артефакты лежат
в `dist-linux/`, логи локальной разработки — в `.build/logs/`.
Linux `.deb` оболочки зависит от `fury-core`: устанавливать нужно оба пакета
из одного комплекта через `sudo apt install ./Fury_*.deb ./fury-core_*_amd64.deb`.
`tools/linux/install.sh` проверяет локальные SHA-256 и устанавливает оба пакета.
Зависимость закреплена на точную версию ядра. При обновлении версии workspace
обновите её в `tauri.linux.conf.json`; `build-shell.sh` проверяет соответствие.

Ядро собирается из Chromium с полной последовательностью патчей Fury:

В Linux-ветке 37 патчей: 36 upstream и `0002-linux-zygote-config.patch`.
Linux создаёт sandboxed renderer/utility процессы через zygote/fork; они обходят
обычный `Initialize()`. Дополнительный патч загружает уже переданный shared-memory
fingerprint после fork, до thread pool и renderer initialization. Sandbox сохраняется.

```sh
J=8 tools/linux/build-core.sh
tools/linux/status.sh
```

Chromium занимает десятки гигабайт, полная сборка требует нескольких часов.
Повторную сборку выполнять в том же output directory. Не подменять ядро обычным
Chrome: оболочка запустится, но антидетект-патчи работать не будут.

`build-core.sh` последовательно получает исходники, применяет патчи, компилирует
и создаёт `.tar.xz` и `.deb` ядра. Повторный запуск использует применённую серию,
если её checksum совпадает; чужие или частично применённые изменения не сбрасываются.
Успех упаковки ещё требует запуска браузера и fingerprint gate.
Загрузчик ограничен четырьмя параллельными jobs (`FURY_SYNC_JOBS`), поскольку
первый проход с upstream defaults получил HTTP 429 от Googlesource.

На машине разработки Chromium tree вынесен в `/home/fury-linux-build-20261016/src`,
а `core/src` является symlink. Это тот же filesystem и тот же checkout с сохранённым
incremental output. Причина: TypeScriptGo подхватывал посторонний пакет
`/home/mdevostator/node_modules/buffer`, после чего Chromium отклонял undeclared
dependency. Родительские `node_modules` не изменялись. При повторении сборки
выбирайте путь исходников без посторонних `node_modules` среди предков.

## Проверка и ограничения

Для первой собственной Linux-персоны откройте в приложении «Настройки» →
«Добавить эту машину в каталог» → «Снять слепок этой машины…», затем
«Использовать на этом компьютере». Нужен обычный Google Chrome на этой машине.
Снимок делается в отдельном временном профиле. Проверочную SwiftShader-персону
из `.build` не следует использовать вместо снимка своего устройства.

- Тесты запускаются с отдельным `FURY_HOME`; рабочие профили пользователя не трогаются.
- Linux capture должен сохранять `os.name = Linux`, `navigator.platform = Linux x86_64`
  и Client Hints Linux. Валидаторы запрещают Direct3D/Metal в Linux-персоне.
  JSON-схема `shared/persona.schema.json` обновлена под текущий формат capture,
  включая Linux, Client Hints, измеренные значения памяти и частоты аудио.
- Встроенный upstream-каталог содержит Windows/macOS. Для Linux нужна собственная
  персона из обычного Chrome на целевой машине; искусственные Windows-конфигурации
  не являются заменой проверки на Linux.
- Сохраняется Chromium sandbox. Не добавлять `--no-sandbox`, не отключать AppArmor
  и не менять глобальные sysctl ради запуска. Ubuntu 24.04 ограничивает user namespaces
  для неизвестных executable; упаковка sandbox и прикладная проверка нужны отдельно.
- Обновления upstream не поставляют Linux-ядро. Не считать кнопку загрузки ядра
  готовым механизмом обновления этого форка.
- Доставка Widevine зависит от локально установленного Chrome; CDM не распространяется.
  Linux размещает его в профиле и атомарно публикует hint для pre-sandbox zygote;
  root-owned каталог ядра остаётся неизменяемым для пользователя.

## Проверено 16.10.2026

- Release `fury-agent` / `fury-detect`, TypeScript/Vite frontend и Tauri `.deb`
  собраны на Ubuntu 24.04 x86_64. Установленное приложение открыто под Xvfb,
  обнаружило системное ядро и подключилось к агенту. Локальный snapshot:
  `.build/qa/installed-desktop/desktop.png`.
- Chromium **155.0.8059.39**, upstream commit
  `3ff7ac5a9224be9156d7f8703a06e22890aafd34`, собран с 37 патчами,
  official release / PGO phase 2 / ThinLTO / CFI. `chrome --version` возвращает
  `Fury 155.0.8059.39`. Зависимости ELF проверены `dpkg-shlibdeps`.
- Содержимое реального `.deb` прошло `verify-core.mjs`: Linux platform/Client Hints,
  `webdriver=false`, 9 контекстов с 0 расхождений, стабильные WebGL1/2,
  сохранение cookies и Canvas после перезапуска, загрузка локального Widevine.
  Canvas: seed 73 → `c06f416c`; seed 74 → `5c4ea2aa`; повторный seed 73 → `c06f416c`.
  Raw captures и summary находятся в `.build/qa/fury-core-final/` (private/ignored).
- Во всех шести captures release gate: **12 PASS / 0 FAIL / 1 skip**.
  Пропущен WebGPU, отсутствующий в этой software-GPU сессии; аппаратный WebGPU
  этим результатом не подтверждается. Лог: `.build/logs/fury-release-gate.log`.
- Sandbox: SUID, PID/network namespaces, Seccomp-BPF/TSYNC и Yama включены.
  После установки `/usr/lib/fury-core/chrome-sandbox` — root:root, mode 4755.
  AppArmor и глобальные sysctl не изменялись.
- Upstream C++ verification: 0001 (config/контексты), 0010 (navigator),
  0011 (UA/Client Hints), 0020 (screen/CSS/iframe), 0081 (timezone),
  0110 (переносимый ключ cookies) — PASS. Для 0020 использован Xvfb 1600×900,
  чтобы контроль отличался от заданных 1920×1080. Cookies проверены на отсутствие
  plaintext и чтение с тем же/другим ключом; неправильный ключ не останавливает браузер.
- Установленные агент и ядро загрузили `https://example.com/` через HTTP relay
  агента и реальный upstream. Проверка выполнена с отдельным временным профилем,
  без отключения проверки TLS-сертификата. Summary: `.build/qa/web-smoke/SUMMARY.json`.
- 415 unit-тестов прошли: agent 229, platform 20, shared 114, detect 13, desktop 39.
- В отдельной DBus-сессии с разблокированным GNOME Keyring проверены Unix IPC
  mode 0600, создание Linux-профиля, корзина/восстановление, отсутствие открытого
  пароля прокси в SQLite/WAL и расшифровка после перезапуска агента.
- Для хранения секретов нужен работающий Secret Service, например GNOME Keyring.
  В headless-сессии без него upstream vault сообщает о недоступности; такую
  сессию нельзя считать проверенным защищённым хранилищем.
- Получены Chrome captures на Linux. Xvfb без GPU даёт отсутствие WebGL, поэтому
  дополнительная software-rendering capture использует явно включённый SwiftShader.
  Она хранится только как локальная QA-персона и не выдаётся за обычное устройство.
- `.github/workflows/ci.yml` дополнен Linux desktop job; удалённый запуск CI ещё
  не выполнялся. Это не проверка Chromium core.
- Проверочный Canvas control переведён на одинаковый ASCII/Arial (probe 0.3.1).
  Stock Chrome 155.0.8059.39 на Linux давал разные emoji fallback в SharedWorker;
  исходный cross-context test ошибочно считал это подменой. Теперь все восемь Canvas
  контекстов stock Chrome совпадают, исключение для ServiceWorker снято. Основной
  Unicode Canvas fingerprint сохранён. `test-sw.mjs` проверяет одинаковый текст
  worker payloads и исправленный no-port reply fallback генератора.
- Negative control: `verify-core.mjs` на обычном Chrome проходит запуск с SUID/
  seccomp sandbox и cross-context проверку, затем ожидаемо отклоняется из-за
  одинакового Canvas у разных seed. Обычный Chrome не выдаётся за Fury core.

При закрытом upstream в QA агент отклонял фоновые обращения Chromium к Google
(`www.google.com`, `content-autofill.googleapis.com`, `android.clients.google.com`,
`accounts.google.com`). Это наблюдение о фоновой сетевой активности; содержимое
этих запросов не исследовалось. Логи локальны в `.build/qa/fury-core-final/`.


## Расширенный прогон 16.10.2026

Повторно проверены установленные пакеты, а не отдельный dev-binary. Прогон
выполнен под X11/Xvfb со SwiftShader, отдельными профилями и GNOME Keyring.
Запущены 33 upstream C++/CDP-сценария. Первый общий прогон дал 25 PASS и 8
неуспешных сценариев; после адресных исправлений тестов и повторов результат
по сценариям — **29 PASS, 4 не подтверждены**. Полный набор не объявляется зелёным.

Проверены передача конфигурации в процессы, navigator/Client Hints, экран,
Canvas/WebGL/audio, timezone/geolocation, permissions, шифрование cookies,
память, мобильный viewport/DPR/клики/сенсоры, ограничения DevTools и чтения
сохранённых паролей, branding и default Safe Browsing preference.
Проверка экспорта закладок через native file dialog в 0303 не автоматизирована
самим upstream-тестом и этим прогоном не подтверждается.

| Сценарий | Итог и ограничение |
|---|---|
| 0050, фильтрация шрифтов | 8/8 PASS после выбора двух измеримо доступных шрифтов вместо обязательного macOS Papyrus |
| 0131, мобильный viewport | 10/10 PASS после учёта classic scrollbar: visualViewport сравнивается с clientWidth при scale=1 |
| 0131-dpr | 28/28 PASS на виртуальном экране 2×: Xvfb 3200×1800 и QA-only force-device-scale-factor=2 |
| 0900, branding | 6/6 PASS: Linux проверяет имя executable через version output, macOS сохраняет проверки app bundle; имя Fury отсутствует в web-visible полях страницы и worker |
| 0041, голоса | Не подтверждён: стенд возвращает 0 голосов, контроль фильтрации невозможен |
| 0060, медиоустройства | Не подтверждён: стенд возвращает 0 входов/выходов, сужать список нечего |
| 0070, WebRTC | Не подтверждён: контрольный запуск не получает ICE-кандидатов; отсутствие утечки в таком контроле не доказывает действие политики |
| 0121, батарея | Не подтверждён: стационарный стенд сообщает питание от сети/100%, тест требует отличающегося состояния батареи |

Ещё три сценария не запускались: 0032 требует доступного WebGPU adapter,
0903 проверяет macOS, а контроль 0902 намеренно отключает sandbox. В этом прогоне
sandbox сохранялся. Виртуальный DPR не является проверкой физического HiDPI GPU.

Дополнительно снова прошли GUI startup с обнаружением пакетного ядра,
создание/корзина/восстановление профиля, шифрование proxy secret и чтение после
рестарта агента, sandbox, WebGL1/2, Widevine из локального Chrome, сохранение
Canvas/cookies после перезапуска и HTTPS example.com через агент.
Во всех шести новых captures gate: **12 PASS / 0 FAIL / 1 skip**; skip — WebGPU.

Raw logs, captures, screenshot и итоговый JSON остаются локально в
.build/qa/validation-20261016T185631Z/ и не публикуются в репозитории.
Аппаратный GPU, Wayland и Linux team-mode E2E этим прогоном не проверены.
