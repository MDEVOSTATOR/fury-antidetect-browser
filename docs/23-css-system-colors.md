# CSS system colours: Windows-персона на Linux

Дата работы: **02.11.2026**. Исправление собрано, проверено и установлено:
**fury-core 0.4.5+linux2**, Chromium 155.0.8059.39, 38 патчей.
Код: [331e8ff](https://github.com/MDEVOSTATOR/fury-antidetect-browser/commit/331e8ff).
Нативный Windows сохраняет свой путь, адаптация проверена на Linux.

## Исходный отчёт и воспроизведение

Коллега сообщил, что Windows-персона на Linux раскрывает host OS через
цвета ссылок. Источники: [rebrowser detector](https://bot-detector.rebrowser.net/)
и [предложенный patch](https://pastebin.com/8LkDSvD0).

На установленном core 0.4.5+linux1 с полной Windows11-персоной удалось получить
Win32 / Client Hints Windows одновременно с ActiveText=rgb(255,0,0).
Публичный detector вернул platformMismatch rating 0.5 и указал именно этот сигнал.
Для чтения отчёта Runtime.enable не использовался.

Минимальное измерение, как на detector:

```js
const el = document.createElement('div');
el.style.setProperty('color-scheme', 'light', 'important');
el.style.setProperty('color', 'ActiveText', 'important');
document.body.appendChild(el);
console.log(navigator.platform, getComputedStyle(el).color);
el.remove();
```

Это CSS keyword ActiveText, а не история посещённых ссылок.
UA-строка сама по себе не определяет эту палитру.

## Причина и выбранное исправление

Pinned Chromium155 задаёт built-in ActiveText красным на Linux; Windows в
светлой схеме использует native COLOR_HOTLIGHT. Стандартное значение Windows10/11 —
rgb(0,102,204). Исходные пути:

- [Chromium Windows CSS mixer](https://chromium.googlesource.com/chromium/src/+/3ff7ac5a9224be9156d7f8703a06e22890aafd34/ui/color/win/css_system_color_mixer_win.cc).
- [Built-in CSS palette](https://chromium.googlesource.com/chromium/src/+/3ff7ac5a9224be9156d7f8703a06e22890aafd34/ui/color/color_provider_utils.cc).
- [Наша новая серия](../core/patches/0022-css-system-colors.patch).

Patch адаптирован к нашей серии, а не выполнен как загруженный script.
Он меняет копию light renderer colour map для config navigator.platform=Win32
на non-Windows-хосте. Linux-персоны и native Windows сохраняют свои пути;
dark и forced maps не заменяются. Полная серия38 патчей переиграна для двух
затронутых файлов с чистой pinned-базы и совпала с рабочим source tree.

| Цвет/внутренний ID | Stock Windows light |
|---|---|
| ActiveText, LinkText, VisitedText, internal Hotlight | rgb(0,102,204) |
| Highlight, internal MenuHilight | rgb(0,120,215) |
| ButtonFace, internal Scrollbar | rgb(240,240,240) |
| GrayText | rgb(109,109,109) |

Hotlight/MenuHilight — внутренние renderer IDs; это не публичные CSS keywords.
Устаревший CSS keyword Scrollbar связан с Canvas и остаётся белым в light scheme;
он не читает одноимённый внутренний renderer ID.
Таблица описывает стандартную палитру, не все пользовательские Windows-темы.

Дополнение к предложенному patch: Linux LayoutTheme применяет BlendWithWhite
к Highlight, Windows возвращает непрозрачный цвет. Для нашего Windows light
provider сохраняется Windows-способ рендеринга. Provider определяется по
сконфигурированной Windows link palette; остальные providers идут прежним путём.
Один CSS vector оформлен отдельным patch, а не изменением patch0132.

## Проверка

Новая регрессия — [verify-0022.py](../core/verify/verify-0022.py).
Используется private loopback fixture, а не рабочие профили:

- native и explicit Linux controls;
- Windows CSS-цвета в main frame, same-origin iframe и отдельном cross-site target;
- реальная Canvas-отрисовка ActiveText;
- dark preference, explicit light и неизменность dark palette;
- включённые forced-colours controls;
- новая вкладка и повторный запуск браузера.

Финальный A/B одним и тем же тестом: старое установленное ядро —
**21 неуспешное утверждение из 53**; исправленный пакет — **53/53 PASS** отдельно
в X11/Xvfb и native Wayland на Weston/Pixman. Это отрицательный контроль,
а не проверка только применения/компиляции patch.

Первоначальное ожидание для legacy CSS Scrollbar было ошибочно взято из
внутреннего renderer ID. Оно исправлено по LayoutTheme Chromium, затем оба
ядра проверены повторно. Ранние логи 24/53 и 3/53 сохранены; финальные результаты
находятся в regression-before-final.log и regression-after-final.log.

| Измерение | Core linux1 | Core linux2 |
|---|---|---|
| ActiveText light | rgb(255,0,0) | rgb(0,102,204) |
| LinkText light | rgb(0,0,238) | rgb(0,102,204) |
| VisitedText light | rgb(85,26,139) | rgb(0,102,204) |
| Highlight light | rgba(0,65,198,0.8) | rgb(0,120,215) |
| rebrowser platformMismatch | rating 0.5, цветовое предупреждение | rating -1, отсутствие этого сигнала |
| Linux / dark / forced controls | Эталон | Контрольные CSS-значения сохранены |

Публичный detector проверен сначала на staged package, затем на установленном
ядре с полной Windows11-персоной; Runtime.enable не вызывался.
Rating-1 здесь относится к platformMismatch, не ко всем тестам сайта.

Дополнительно на новом ядре прошли Linux full probes в обоих backend:
SUID/Seccomp, platform/CH,9 контекстов, WebGL1/2, Canvas, cookies после restart
и локальный Widevine. По6 captures на backend: **12 PASS / 0 FAIL / 1 WebGPU skip**
в каждом. Installed smoke подтвердил Secret Service/private profiles и
реальный SUID/Seccomp sandbox. Физический GPU этим не проверялся.

## Версия, установка и откат

Установленный runtime — fury-core 0.4.5+linux2,38 патчей, Chromium155.0.8059.39.
Только Linux package revision меняется; upstream Fury остаётся0.4.5.
[core/LINUX_PACKAGE_REVISION](../core/LINUX_PACKAGE_REVISION) хранит revision,
build-shell проверяет точную зависимость Tauri, а runtime archive получает r2 в имени.

Оболочка по-прежнему называется Fury_0.4.5_amd64.deb, но зависит ровно от
fury-core 0.4.5+linux2. Installer использует --reinstall, чтобы обновить dependency
при прежней upstream-версии desktop. Candidate тестировался в отдельной root-owned
установке с sandbox helper; рабочая установка обновлена после успешных проверок.
SHA256 установленного ядра совпал с tested staged payload.

build-shell.sh принимает необязательный output directory первым аргументом,
package-core.sh — вторым после build directory. Это позволяет готовить комплект
отдельно от последнего проверенного dist-linux. Пример после сборки Chromium:

```bash
tools/linux/build-shell.sh "$PWD/.build/candidate-css2"
tools/linux/package-core.sh "$PWD/core/src/out/linux-x64.noindex" "$PWD/.build/candidate-css2"
```

Для повторения регрессии в отдельной DBus/keyring/display-сессии из
[handoff](22-linux-handoff.md#как-повторять-qa):

```bash
python3 core/verify/verify-0022.py /usr/lib/fury-core/chrome .build/qa/css-colours
```

Предыдущий комплект с SHA-файлами и BUILD-INFO сохранён локально в
.build/link-colors-review/before-artifacts/. Для осознанного rollback нужны оба
старых .deb; apt должен допустить downgrade core и reinstall прежней оболочки.

Изменение системных цветов Windows-персоны — намеренное изменение её наблюдаемого
отпечатка после обновления. Сам seed не меняется. Новое ядро используется при
следующем запуске профиля.

## Доказательства и границы

Локальные BEFORE.json, regression-before/colours.json, detector-before/SUMMARY.json,
package/build logs находятся в .build/link-colors-review/ и не публикуются в Git.
Итог: .build/link-colors-review/SUMMARY.json, browser-x11/, browser-wayland/,
regression-after-final/, regression-wayland/ и detector-installed/SUMMARY.json.
Проверочная установка из /opt перенесена в retired-runtime-css2/ после снятия
setuid; для будущих запусков используется установленное ядро или новый root-owned
QA-runtime, а не helper внутри writable build tree.

Согласованность этого CSS-вектора не доказывает полной идентичности Windows
на Linux. Hardware GPU, Windows fonts/voices, любые другие результаты detector
и пользовательские forced-colour темы требуют собственных измерений.
