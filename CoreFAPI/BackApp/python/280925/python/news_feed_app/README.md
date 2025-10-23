**Помечаем app как Sources root**

## Разработка

## Запуск docker image

```shell
docker build -t your_image_name .
docker run \
  --network=host \
  --env-file .env \
  --name your_container_name \
  your_tag
```

### Зависимости
Для управления зависимостей, на сервере используется poetry.
Все зависимости поделены на группы _**main, test, dev**_.

#### Установка зависимостей
Чтобы установить основные зависимости из группы main:
```sh
  poetry install
```

Чтобы установить основные зависимости вместе зависимостями из других групп:
```sh
  poetry install --with test
```
Так же можно установить (test,dev без пробела)
```sh
  poetry install --with test,dev
```
Если нужно установить определённую группу зависимостей:

```sh
  poetry install --only dev
```

#### Добавление зависимостей

Чтобы добавить новую зависимость в группу main:
```sh
  poetry add {package_name}
```

Чтобы установить основные зависимости для тестирования:
```sh
  poetry add {package_name} --group test 
```
Чтобы установить основные зависимости для разработки:
```sh
  poetry add {package_name} --dev 
```

#### Удаление зависимостей

Чтобы удалить зависимость из группы main:
```sh
  poetry remove {package_name}
```

Чтобы установить основные зависимости для тестирования:
```sh
  poetry remove {package_name} --group test 
```
Чтобы установить основные зависимости для разработки:
```sh
 poetry remove {package_name} --dev
```

# 🐇 RabbitMQ: 

## Внешние задачи:

### Уведомления об упоминаниях пользователей:

Сервис отправляет события об **упоминаниях пользователей** (`@username`) в RabbitMQ — для последующей обработки.

### 📦 Пример сообщения

Сообщения отправляются в очередь **news_feed** в формате JSON:

```json
{
  "type": "mentioning_users",
  "type_mention": "post",
  "event_mention": "create",
  "usernames": ["username1", "username2"],
  "post_id": 1,
  "comment_id": null
}
```

- type: тип задачи (в данном случае - `mentioning_users` упоминание пользователей)
- type_mention: post или comment
- event_mention: create, update или delete
- usernames: список имён пользователей без @
- post_id: ID поста
- comment_id: ID комментария, если type_mention = comment

Примечание: При update задача будет создаваться всегда, даже с usernames: [тут пусто]. 
Для проверки, вдруг уведомление было создано раньше, а теперь обновили без упоминаний пользователей и уведомление нужно удалить.

### Уведомления о новых подписчиках:

Сервис отправляет события о новых подписках в очередь RabbitMQ.

### 📦 Пример сообщения

Сообщения отправляются в очередь **news_feed** в формате JSON:

```json
{
  "type": "new_subscriber",
  "author_id": "3d6f0a49-bf6b-4f6a-bf9c-842b42e4f462",
  "subscriber_id": "84d02b3c-e7cf-4a97-a7f2-534bbf9ef24e"
}
```

- type: тип задачи (в данном случае - `new_subscriber` новый подписчик)
- author_id: уникальный идентификатор автора, на которого подписываются
- subscriber_id: уникальный идентификатор пользователя, который подписался

### Уведомления о новых сообщениях под постом:

Сервис отправляет события о новых сообщениях под постом в очередь RabbitMQ.

### 📦 Пример сообщения

Сообщения отправляются в очередь **news_feed** в формате JSON:

```json
{
  "type": "new_comment",
  "author_id": "3d6f0a49-bf6b-4f6a-bf9c-842b42e4f462",
  "user_id": "84d02b3c-e7cf-4a97-a7f2-534bbf9ef24e",
  "post_id": 1,
  "comment_id": 3
}
```

- type: тип задачи (в данном случае - `new_comment` новое сообщение)
- author_id: ID автора поста
- user_id: ID пользователя, который оставил комментарий
- post_id: ID поста, под которым был оставлен комментарий
- comment_id: ID комментария

### Уведомления о новых постах:

Сервис отправляет события о новых постах в очередь RabbitMQ.

### 📦 Пример сообщения

Сообщения отправляются в очередь **news_feed** в формате JSON:

```json
{
  "type": "new_post",
  "post_id": 3,
  "author_id": "84d02b3c-e7cf-4a97-a7f2-534bbf9ef24e",
  "subscribers_ids": ["aa04931c-f4cf-4c4c-ab5a-8195fc7892b5", "ec3e547b-a5b0-4708-b784-96d13e06c60d"]
}
```

- type: тип задачи (в данном случае - `new_post` новый пост)
- post_id: ID нового поста
- author_id: ID пользователя, который создал пост
- subscribers_ids: Список из ID пользователей, которые подписаны на автора поста

### Уведомления о новых лайках:

Сервис отправляет события о новых лайках в очередь RabbitMQ.

### 📦 Пример сообщения

Сообщения отправляются в очередь **news_feed** в формате JSON:

```json
{
  "type": "new_like",
  "type_object": "comment",
  "user_id": "84d02b3c-e7cf-4a97-a7f2-534bbf9ef24e",
  "post_id": 2,
  "author_id": "aa04931c-f4cf-4c4c-ab5a-8195fc7892b5",
  "comment_id": 33
}
```

- type: тип задачи (в данном случае - `new_like` новый лайк)
- type_object: тип лайка ("post" или "comment")
- user_id: ID пользователя, который поставил лайк
- post_id: ID поста, которому поставили лайк (или к которому принадлежит комментарий, если это лайк комментария)
- author_id: ID автора поста или комментария
- comment_id: ID комментария, если это лайк комментария, иначе None
