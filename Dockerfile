# This image provides the binaries for node, npm, and npx
FROM node:19 AS node_base

# Download and extract the elm binaries
WORKDIR /usr/local/bin
RUN wget -c https://github.com/lydell/elm-old-binaries/releases/download/main/0.18.0-linux-x64.tar.gz -O - | tar -xz
RUN ./dist_binaries/elm --version

# This is the image the container is actually built from
# We'll take the Python environment and add node and elm to it
FROM python:3.10

# Environment
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Python dependencies
WORKDIR /app
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Node, npm binaries
COPY --from=node_base /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node_base /usr/local/bin/node /usr/local/bin/node
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm
RUN ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
RUN node --version && npm --version

# Copy elm binaries
COPY --from=node_base /usr/local/bin/dist_binaries/* /usr/local/bin/
RUN elm --version

# Node dependencies
COPY package.json package-lock.json ./
RUN npm install

# Elm dependencies
COPY learnscripture/static/elm ./learnscripture/static/elm
WORKDIR /app/learnscripture/static/elm
RUN npx elm-install
WORKDIR /app/learnscripture/static/elm/tests
RUN npx elm-install

CMD sleep infinity
