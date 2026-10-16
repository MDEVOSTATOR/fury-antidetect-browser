# Linux x86_64 port

Рабочая ветка: `port/linux-x64`, база Fury 0.4.5 (`a813065`). Целевая система
для первой сборки: Ubuntu 24.04 x86_64, GTK 3 / WebKitGTK 4.1. Поддержку других
дистрибутивов и Wayland нужно проверять отдельно.

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

Ядро собирается из Chromium с полной последовательностью патчей Fury:

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
  собраны на Ubuntu 24.04 x86_64. Окно приложения отрисовано под Xvfb; snapshot
  находится локально в `.build/qa/linux-desktop.png`.
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

Статус этой страницы описывает порт в разработке. Итоговые результаты сборки,
запуска и fingerprint gate должны быть внесены после фактической проверки.
