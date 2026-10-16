# Upstream issues и Linux-форк — 16.10.2026

Проверены все 16 записей issues/PR исходного репозитория, включая закрытые,
комментарии и merge status. На момент проверки upstream main не содержит
новых коммитов поверх базы нашего форка.

| Источник | Состояние upstream | Решение в Linux-форке |
|---|---|---|
| [PR #10: Linux Wayland и hardening](https://github.com/furyteamtop/fury-antidetect-browser/pull/10) | Closed, **не merged** | Выборочно адаптированы Ozone backend selection, проверенный TLS к HTTPS-прокси и диагностика TLS |
| [Issue #16: WebGL extension gating](https://github.com/furyteamtop/fury-antidetect-browser/issues/16) | Closed, выпущено в upstream 0.2.24 | Исправление уже в нашей базе; verify-0031 прошёл расширенный прогон |
| [Issue #4](https://github.com/furyteamtop/fury-antidetect-browser/issues/4), [PR #9: MMDB](https://github.com/furyteamtop/fury-antidetect-browser/pull/9) | Closed, PR merged | Локальный GeoIP уже в базе; повторно не переносился |
| [Issues #11](https://github.com/furyteamtop/fury-antidetect-browser/issues/11), [#12](https://github.com/furyteamtop/fury-antidetect-browser/issues/12), [PR #13](https://github.com/furyteamtop/fury-antidetect-browser/pull/13) | Open; C++ ещё не скомпилирован и не измерен, PR рассчитан на более ранний Chromium155 | Не переносился. Требует отдельного review, пересборки ядра и runtime-проверок font local() и NetworkInformation |
| Остальные записи | Персоны, расширения, Homebrew, сравнение Camoufox и dependency updates | Отдельных готовых исправлений Linux не обнаружено |

## Что изменилось

Агент на Linux добавляет ozone-platform=wayland, когда WAYLAND_DISPLAY непустой.
Для совместимости можно явно задать FURY_OZONE_PLATFORM=x11. Явное значение
имеет приоритет; без Wayland и без override сохраняется стандартный выбор Chromium.
Оба backend уже были включены в нашем ядре, поэтому Chromium не пересобирался.
Это выбор при запуске, а не автоматический повтор с другим backend при ошибке.

HTTPS-прокси теперь получает проверенный TLS-сеанс **до** HTTP CONNECT и
Proxy-Authorization. Раньше схема https принималась как обычный HTTP/TCP,
хотя проверка прокси через reqwest умела TLS. Ошибка сертификата или имени
завершает подключение; downgrade в HTTP и прямой выход не выполняются.
Диагностика HTTPS не предлагает заменить схему ради обхода TLS-ошибки.

Широкий PR #10 целиком не сливался: server RBAC/transfer, proxy-paste UI,
AppImage/release workflows и другие части требуют отдельной проверки.
Наш формат доставки — два Debian-пакета; AppImage-specific GTK hook не применялся.
Проверка совместимости ядра в PR также не переносилась: наш системный runtime
согласуется точной Debian-зависимостью, а политику custom cores нужно менять отдельно.

## Проверка до установки

- cargo test -p fury-agent: **236 PASS / 0 FAIL**.
- Release-agent на native Wayland: отдельный Weston13 headless/Pixman, DISPLAY
  удалён, в реальной command line браузера проверен ozone-platform=wayland.
- Release-agent с FURY_OZONE_PLATFORM=x11: Xvfb, одновременно задан WAYLAND_DISPLAY;
  реальная command line содержит ozone-platform=x11.
- В каждом backend: sandbox SUID/Seccomp, Linux navigator/CH, webdriver=false,
  согласованность контекстов, WebGL1/2, стабильность/различие Canvas,
  cookies и отпечаток после перезапуска, локальный Widevine — PASS.
- Release CLI HTTPS relay на loopback: authenticated CONNECT и payload внутри
  TLS с доверенной тестовой CA; недоверенный сертификат и несовпадение hostname
  дают 502, до rejected proxy не доходит Proxy-Authorization. Test CA добавлялась
  только в окружение процесса, системное хранилище сертификатов не менялось.

После пересборки Debian-пакета обновлена локальная установка. SHA256 установленного
агента совпадает с протестированным release-binary. Нативное окно установленного
Fury открыто на том же программном Wayland compositor без DISPLAY; агент подключён,
пакетное ядро обнаружено, получен и визуально проверен compositor screenshot.
Для software WebKit smoke задан WEBKIT_DISABLE_DMABUF_RENDERER=1 только в QA-окружении.

Это проверка на программном Wayland compositor, не hardware GPU,
не интерактивная GNOME/KDE/Hyprland-сессия и не подтверждение всех desktop-функций.
Raw captures и TLS fixtures остаются локальными; исходные регрессии находятся
в agent tests. Для проверки выбранного backend verify-core.mjs принимает
FURY_QA_OZONE_PLATFORM=wayland или x11.
