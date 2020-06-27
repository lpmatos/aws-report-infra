ARG PYTHON_VERSION=3.8-alpine3.11

FROM python:${PYTHON_VERSION} as base
FROM base as install-env

COPY [ "requirements.txt", "."]

RUN pip install --upgrade pip && \
    pip install --user --no-warn-script-location -r ./requirements.txt

FROM base

LABEL maintainer="Lucca Pessoa da Silva Matos - luccapsm@gmail.com" \
        org.label-schema.version="1.0.0" \
        org.label-schema.release-data="25-06-2020" \
        org.label-schema.url="https://github.com/lpmatos/aws-report-infra" \
        org.label-schema.name="AWS Report Infra"

RUN set -ex && apk update && \
    apk add --update --no-cache bash=5.0.11-r1

COPY --from=install-env [ "/root/.local", "/usr/local" ]

WORKDIR /usr/src/code

COPY [ "./code", "." ]

RUN mkdir files && \
    find ./ -iname "*.py" -type f -exec chmod a+x {} \; -exec echo {} \;;
