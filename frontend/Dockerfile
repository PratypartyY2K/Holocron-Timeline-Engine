FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json tsconfig.json next.config.ts next-env.d.ts /app/
COPY app /app/app
COPY components /app/components
COPY lib /app/lib

RUN npm ci

CMD ["npm", "run", "dev"]
