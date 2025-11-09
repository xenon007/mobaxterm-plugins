# Awesome MobaXterm Plugins

> Подборка сторонних плагинов и утилит, которые удобно использовать в портативной среде [MobaXterm](https://mobaxterm.mobatek.net/). Коллекция сгруппирована по тематическим направлениям и следует структуре awesome-листов.

## Содержание
- [DevOps](#devops)
- [FRNC / DevSecOps](#frnc--devsecops)
- [Как пользоваться](#как-пользоваться)
- [Как добавить новый плагин](#как-добавить-новый-плагин)
- [Лицензия](#лицензия)

## DevOps

- [Kubectl 1.20.4](https://kubernetes.io/docs/tasks/tools/) — CLI для управления кластерами Kubernetes. Версия соответствует релизу `v1.20.4`.
- [OC Tool 3.11 / 4.x](https://www.okd.io/) — клиент OpenShift для работы с кластерами OKD/OpenShift.
- [MinIO RELEASE.2021-03-10T05-11-33Z](https://github.com/minio/minio/releases/tag/RELEASE.2021-03-10T05-11-33Z) — self-hosted S3-совместимое хранилище, включает сервер и клиент.
- [k9s 0.24.2](https://github.com/derailed/k9s/releases/tag/v0.24.2) — TUI для интерактивного управления ресурсами Kubernetes.
- [ktunnel 1.3.5](https://github.com/omrikiei/ktunnel/releases/tag/1.3.5) — CLI, открывающий доступ к локальным ресурсам из кластера Kubernetes.
- [kubebox 0.9.0](https://github.com/astefanutti/kubebox/releases/tag/v0.9.0) — терминальный и веб-интерфейс для Kubernetes.
- [kubectl-tree](https://github.com/ahmetb/kubectl-tree/releases) — плагин kubectl для просмотра иерархии объектов Kubernetes в виде дерева.
- [kubectl-aliases](https://ahmet.im/blog/kubectl-aliases/) — автоматически сгенерированные alias-команды для kubectl ([сырой файл](https://raw.githubusercontent.com/ahmetb/kubectl-aliases/master/.kubectl_aliases)).
- [KubeVela 0.3.2](https://github.com/oam-dev/kubevela/releases/tag/v0.3.2) — платформенный движок на основе Kubernetes и Open Application Model.
- [stern 1.11.0](https://github.com/wercker/stern/releases/tag/v1.11.0) — tail-утилита для логов сразу из нескольких pod и контейнеров.
- [kind 0.10.0](https://github.com/kubernetes-sigs/kind/releases/tag/v0.10.0) — запуск локальных Kubernetes-кластеров в Docker.
- [kops 1.19.1](https://github.com/kubernetes/kops/releases/tag/v1.19.1) — управление жизненным циклом production-кластеров Kubernetes.
- [minikube 1.18.1](https://github.com/kubernetes/minikube/releases/tag/v1.18.1) — запуск локального Kubernetes на рабочей станции.
- [Argo Workflows 2.12.10](https://github.com/argoproj/argo-workflows/releases/tag/v2.12.10) — движок workflow'ов для Kubernetes.
- [Argo CD 1.7.14](https://github.com/argoproj/argo-cd/releases/tag/v1.7.14) — GitOps-инструмент для декларативного деплоя приложений.
- [Flux 1.21.2](https://github.com/fluxcd/flux/releases) — GitOps-оператор Kubernetes.
- [Flux v2 0.9.1](https://github.com/fluxcd/flux2/releases/tag/v0.9.1) — расширяемое решение непрерывной доставки на базе GitOps Toolkit.
- [k8s-image-swapper 1.0.0](https://github.com/estahn/k8s-image-swapper/releases/tag/v1.0.0) — автоматическое зеркалирование и подмена ссылок на образы контейнеров.
- [Reloader 0.0.84](https://github.com/stakater/Reloader/releases/tag/v0.0.84) — контроллер, выполняющий rolling-update при изменениях ConfigMap и Secret.
- [skaffold 1.20.0](https://github.com/GoogleContainerTools/skaffold/releases/tag/v1.20.0) — автоматизация цикла разработки и деплоя Kubernetes-приложений.
- [werf 1.2.9f8](https://github.com/werf/werf/releases) — GitOps-платформа доставки приложений.
- [tanka 0.14.0](https://github.com/grafana/tanka/releases/tag/v0.14.0) — модульная декларативная конфигурация Kubernetes на базе Jsonnet.
- [kubenav 3.4.0](https://github.com/kubenav/kubenav/releases/tag/v3.4.0) — кросс-платформенный клиент для управления Kubernetes-кластерами.
- [kubeseal 0.15.0](https://github.com/bitnami-labs/sealed-secrets/releases/tag/v0.15.0) — шифрование и управление секретами с помощью sealed-secrets.

## FRNC / DevSecOps

- [YARA 4.3.1](https://github.com/VirusTotal/yara/releases/tag/v4.3.1) — инструмент для классификации и идентификации вредоносных образцов.

## Как пользоваться

1. Скачайте архив плагина из релиза по соответствующей ссылке.
2. Распакуйте содержимое в директорию `MobaXterm/Plugins` или другую рабочую папку.
3. Перезапустите MobaXterm — плагин появится в списке доступных утилит.
4. При необходимости настройте переменные окружения и путевые переменные в настройках MobaXterm.

## Как добавить новый плагин

1. Форкните репозиторий и создайте ветку с говорящим названием.
2. Добавьте информацию о плагине в соответствующий раздел, соблюдая формат `- [Имя](ссылка) — описание (версия).`
3. При необходимости разместите связанные файлы в каталоге `data/` или `docs/`.
4. Оформите pull request с кратким описанием изменений.

## Лицензия

См. файл [LICENSE](LICENSE). Список распространяется по [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/), что соответствует духу большинства awesome-листов.
