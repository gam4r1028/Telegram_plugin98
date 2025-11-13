"""Conversation logic for the Stranger Things Farewell experience."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class GameOption:
    key: str
    description: str
    next_node: str


@dataclass
class GameNode:
    text: str
    options: List[GameOption]
    ending: Optional[str] = None
    epilogue: Optional[str] = None


class StrangerThingsFarewell:
    """Keeps track of nostalgic conversations for each chat."""

    def __init__(self) -> None:
        self._sessions: Dict[int, Dict[str, str]] = {}
        self._mini_game_nodes = self._build_mini_game()

    @staticmethod
    def _warning_message() -> str:
        return (
            "Внимание, дальше могут быть спойлеры по Stranger Things. "
            "Вы согласны продолжить? (да/нет)"
        )

    def start(self, chat_id: int) -> List[str]:
        self._sessions[chat_id] = {"state": "await_confirmation"}
        return [
            "Я снова в Хоукинсе и готов делиться воспоминаниями!",
            self._warning_message(),
        ]

    def stop(self, chat_id: int) -> List[str]:
        if chat_id in self._sessions:
            self._sessions.pop(chat_id, None)
            return [
                "Бот остановлен. Если захочешь вернуться в Хоукинс — напиши .strange",
            ]
        return [
            "Мы и так молчали, но я всегда рядом. Как решишь вернуться — набери .strange",
        ]

    def handle_message(self, chat_id: int, text: str) -> List[str]:
        text = (text or "").strip()
        if not text:
            return []

        session = self._sessions.get(chat_id)
        if not session:
            return []

        state = session.get("state")
        if state == "await_confirmation":
            return self._handle_confirmation(chat_id, session, text)
        if state == "main_menu":
            return self._handle_menu(chat_id, session, text)
        if state == "mini_game":
            return self._handle_mini_game(chat_id, session, text)
        return []

    def _handle_confirmation(self, chat_id: int, session: Dict[str, str], text: str) -> List[str]:
        lowered = text.lower()
        if lowered in {"да", "д", "конечно", "ага", "yes", "ок", "хочу"}:
            session["state"] = "main_menu"
            return [
                "Отлично! Давай разворошим архив воспоминаний.",
                self._menu_text(),
            ]
        if lowered in {"нет", "н", "неа", "no", "потом"}:
            self._sessions.pop(chat_id, None)
            return [
                "Понимаю. Если захочешь вновь окунуться в атмосферу Хоукинса — зови .strange",
            ]
        return [
            "Это серьёзный момент. Напиши просто "
            "\"да\" или \"нет\", чтобы я понял, готов ли ты к воспоминаниям.",
        ]

    def _handle_menu(self, chat_id: int, session: Dict[str, str], text: str) -> List[str]:
        if text == "0":
            return self._all_seasons_response()

        summaries = self._season_summaries()
        season = summaries.get(text)
        if season:
            return [season, self._menu_reminder()]

        if text == "6":
            return [self._farewell_text(), self._menu_reminder()]

        if text == "7":
            session["state"] = "mini_game"
            session["node"] = "intro"
            intro = self._mini_game_nodes["intro"]
            return [
                "Добро пожаловать в маленькое приключение. Ты — новый житель Хоукинса.",
                self._format_game_node(intro),
            ]

        return [
            "Кажется, здесь нет такого пункта. Напиши цифру из меню, чтобы продолжить.",
            self._menu_text(),
        ]

    def _handle_mini_game(self, chat_id: int, session: Dict[str, str], text: str) -> List[str]:
        node_name = session.get("node")
        node = self._mini_game_nodes.get(node_name or "")
        if not node:
            session["state"] = "main_menu"
            return [self._menu_text()]

        option = next((opt for opt in node.options if opt.key == text), None)
        if not option:
            return [
                "Странный выбор. Попробуй снова и используй цифры из вариантов.",
                self._format_game_node(node),
            ]

        next_node = self._mini_game_nodes.get(option.next_node)
        if not next_node:
            session["state"] = "main_menu"
            return [self._menu_text()]

        session["node"] = option.next_node

        if next_node.ending:
            session["state"] = "main_menu"
            session.pop("node", None)
            responses = [next_node.text, next_node.ending]
            if next_node.epilogue:
                responses.append(next_node.epilogue)
            responses.append("Вернёмся к меню воспоминаний?")
            responses.append(self._menu_text())
            return responses

        return [self._format_game_node(next_node)]

    def _all_seasons_response(self) -> List[str]:
        lines = [
            "Поехали по всем сезонам — будто пересматриваем кассеты подряд:",
        ]
        summaries = self._season_summaries()
        for key in ("1", "2", "3", "4", "5"):
            lines.append(summaries[key])
        lines.append(
            "Вот таким путём мы пришли к финалу. Выбирай, что хочется обсудить дальше."
        )
        return ["\n\n".join(lines), self._menu_reminder()]

    def _menu_text(self) -> str:
        return (
            "Выбирай, куда заглянем дальше:\n"
            "0 — пересказать все сезоны по очереди\n"
            "1. Сезон 1 — начало легенды\n"
            "2. Сезон 2 — развитие мифологии и угрозы\n"
            "3. Сезон 3 — лето, Starcourt, лёгкий и яркий вайб\n"
            "4. Сезон 4 — мрачный хоррор, Векна, масштаб\n"
            "5. Сезон 5 — ожидания и известные факты\n"
            "6. Прощание с сериалом\n"
            "7. Сюжетная мини-игра"
        )

    @staticmethod
    def _menu_reminder() -> str:
        return "Если хочешь продолжить, просто напиши цифру из меню."

    @staticmethod
    def _season_summaries() -> Dict[str, str]:
        return {
            "1": (
                "Сезон 1 — начало легенды. Мальчик пропадает, "
                "а его друзья запускают приключение, где верность важнее всего. "
                "Элевен с хрупкой силой, Хоппер с грубоватой заботой, Джойс, "
                "которая готова разговаривать с лампочками ради сына. Атмосфера — "
                "детская смелость и 80-е, где за велосипедами скрываются порталы. "
                "Именно тогда Хоукинс впервые понял, что мир больше и страшнее."),
            "2": (
                "Сезон 2 — развитие мифологии и угрозы. Тени и Шёпоты Зазеркалья "
                "прорастают в Уилла, а дружба проверяется на прочность, когда "
                "каждому приходится взрослеть. Новенький Макс привносит искру, "
                "Стив неожиданно становится лучшим нянькой, а над городом висит "
                "ощущение, что зло учится и ждёт подходящего момента. Это сезон "
                "про то, как хрупкие подростковые сердца становятся щитом."),
            "3": (
                "Сезон 3 — лето, Starcourt, неоновый шум и тайные бункеры. "
                "Друзья пробуют себя во взрослых отношениях, но всё ещё готовы "
                "взяться за рации и мороженое, чтобы спасти мир. Робин и Эрика "
                "добавляют саркастичный свет, а под улыбкой торгового центра скрывается "
                "тревога. Это самый яркий и тёплый сезон, который всё равно "
                "заканчивается слезами под пожухлыми фейерверками."),
            "4": (
                "Сезон 4 — мрачный хоррор. Векна приходит через травмы, "
                "вытаскивая наружу то, о чём стараешься не думать. Макс с кассетой "
                "в руках, Нэнси с расследованием, Стив — бесконечный защитник, "
                "Эдди, который на сцене и в бою одинаково честен. Атмосфера "
                "кошмаров, где музыка спасает буквально. Хоукинс трещит, и герои "
                "понимают, что детство осталось позади."),
            "5": (
                "Сезон 5 — ещё впереди. Мы знаем лишь обрывки: команда снова "
                "вместе, Векна не сказал последнего слова, а финал обещает объединить "
                "все ниточки, за которые мы держались долгие годы. Это ожидание, "
                "замершее между страхом и надеждой, когда понимаешь, что "
                "последний рывок будет самым важным."),
        }

    @staticmethod
    def _farewell_text() -> str:
        return (
            "Прощание с сериалом. Помнишь, как всё началось с тихого городка, "
            "где дети играли в Dungeons & Dragons, а взрослые пытались справиться с "
            "собственными потерями? Мы видели, как они взрослели, как страхи менялись, "
            "как смех становился глубже, потому что за ним стояли настоящие травмы. "
            "Stranger Things подарил нам дружбу, которая выдержала монстров, "
            "любовь, которая не боится расстояний, и веру в то, что даже в "
            "самой тёмной ночи найдётся фонарик. Финал — это не про то, что всё "
            "кончится. Это про то, что история останется с нами, как старая кассета, "
            "которую можно перемотать и включить снова, когда захочется ощутить "
            "тот самый запах лета и звуки синтезатора."
        )

    def _build_mini_game(self) -> Dict[str, GameNode]:
        return {
            "intro": GameNode(
                text=(
                    "Ты приезжаешь в Хоукинс в конце лета 1986-го. В городе висит "
                    "чувство, будто воздух электрический. На площади ты замечаешь "
                    "трёх ребят из клуба АВ, машущих тебе."
                ),
                options=[
                    GameOption("1", "Подойти и узнать, чем они заняты", "club"),
                    GameOption("2", "Проигнорировать и прогуляться к Старкорту", "mall"),
                    GameOption("3", "Пойти к озеру Лавона — говорят, там странно", "lake"),
                ],
            ),
            "club": GameNode(
                text=(
                    "Ребята радостно принимают тебя. Они ищут человека, способного "
                    "держать рацию и не бояться ночных вылазок."
                ),
                options=[
                    GameOption("1", "Согласиться и отправиться на ночное патрулирование", "patrol"),
                    GameOption("2", "Вежливо отказаться — слишком уж это опасно", "quiet_life"),
                ],
            ),
            "mall": GameNode(
                text=(
                    "Старкорт закрыт, но у заднего входа слышны голоса. Это Макс "
                    "и Лукас спорят, стоит ли снова лезть в неприятности."
                ),
                options=[
                    GameOption("1", "Подслушать разговор и предложить помощь", "team_up"),
                    GameOption("2", "Развернуться — ты не для таких подвигов", "quiet_life"),
                ],
            ),
            "lake": GameNode(
                text=(
                    "У воды туманно, словно кто-то включил генератор дыма. Из-за деревьев "
                    "выходит Робин с гитарой Эдди и просит помочь настроить аппаратуру."
                ),
                options=[
                    GameOption("1", "Помочь и расспросить, зачем им музыка ночью", "music"),
                    GameOption("2", "Сказать, что не умеешь, и вернуться домой", "quiet_life"),
                ],
            ),
            "quiet_life": GameNode(
                text=(
                    "Ты выбираешь спокойствие. Вечером смотришь на огоньки Хоукинса из окна."
                ),
                options=[],
                ending=(
                    "Иногда это тоже подвиг — признать, что не готов к теням. Ты остаёшься "
                    "наблюдателем, но при первой же сирене готов схватить рацию."
                ),
                epilogue="Город продолжает жить, а ты постепенно становишься его частью.",
            ),
            "patrol": GameNode(
                text=(
                    "Ночь пахнет сырой землёй. Вместе с Дастином и Макс вы слышите "
                    "мерцающий гул из-под земли."
                ),
                options=[
                    GameOption("1", "Спуститься в тоннель без промедления", "tunnel"),
                    GameOption("2", "Сначала позвать Хоппера по рации", "hopper"),
                ],
            ),
            "team_up": GameNode(
                text=(
                    "Твои слова убеждают ребят, что новый союзник не помешает. Вы решаете "
                    "проверить заброшенный аттракцион, где по ночам слышен смех."
                ),
                options=[
                    GameOption("1", "Войти внутрь одними первыми", "funhouse"),
                    GameOption("2", "Обойти вокруг и искать следы", "perimeter"),
                ],
            ),
            "music": GameNode(
                text=(
                    "Робин объясняет: звук — лучшая защита. Вы устраиваете мини-концерт, "
                    "чтобы отвлечь взгляд из Изнанки."
                ),
                options=[
                    GameOption("1", "Играть громко и смело", "loud_finale"),
                    GameOption("2", "Сыграть тихо, чтобы не напугать никого", "soft_finale"),
                ],
            ),
            "tunnel": GameNode(
                text=(
                    "Под городом тепло и страшно. Ты видишь мерцающие споры и понимаешь: "
                    "ещё шаг — и назад не вернёшься."
                ),
                options=[],
                ending=(
                    "Ты делаешь шаг вперёд и направляешь свет фонаря. Существо "
                    "отступает, и вы закрываете проход. Хоукинс запоминает тебя героем."
                ),
                epilogue="На следующий день друзья дарят тебе собственную рацию.",
            ),
            "hopper": GameNode(
                text=(
                    "Хоппер ворчит, но приезжает. Вместе вы закрываете тоннель, пока "
                    "он не расширился."
                ),
                options=[],
                ending=(
                    "Ты понимаешь, что сила — в команде. Тебя приглашают в семейный "
                    "ужин у Байерсов, где за столом смеются и спорят."
                ),
                epilogue="Ты чувствуешь себя частью истории, даже если не был в центре.",
            ),
            "funhouse": GameNode(
                text=(
                    "Внутри зеркала и запах сладкой ваты. В отражении появляется силуэт, "
                    "который не повторяет ваши движения."
                ),
                options=[],
                ending=(
                    "Ты разбиваешь зеркало, и сущность исчезает. Но один осколок сохраняешь "
                    "как напоминание, что смелость иногда рождается из страха."
                ),
                epilogue="Макс говорит, что с тобой не страшно даже в самых кривых отражениях.",
            ),
            "perimeter": GameNode(
                text=(
                    "Снаружи находите следы ботинок и странную слизь. След ведёт к лесу."
                ),
                options=[
                    GameOption("1", "Отправиться по следу", "forest_chase"),
                    GameOption("2", "Сообщить остальным и ждать подкрепление", "hopper"),
                ],
            ),
            "forest_chase": GameNode(
                text=(
                    "Лес звучит чужим эхом. Существо выскакивает из портала, и "
                    "тебе приходится тянуть друзей к машине."
                ),
                options=[],
                ending=(
                    "Вы уносите ноги, но понимаете: иногда выжить — тоже победа. "
                    "Теперь у тебя есть любимая байка для лагерного костра."
                ),
                epilogue="В клубе АВ тебя слушают с открытыми ртами и предлагают место за столом.",
            ),
            "loud_finale": GameNode(
                text=(
                    "Музыка гремит, и ты почти видишь, как невидимая тень пятится назад."
                ),
                options=[],
                ending=(
                    "Вы спасаете дежурящую ночную смену от кошмара, и на утро город "
                    "звучит чуть ярче. Ты просыпаешься с хриплым голосом и гордостью."
                ),
                epilogue="Эдди бы тобой гордился — гитара теперь и твой символ.",
            ),
            "soft_finale": GameNode(
                text=(
                    "Ты выбираешь играть нежно. Музыка превращается в lullaby, и "
                    "туман расходится."
                ),
                options=[],
                ending=(
                    "Иногда Хоукинсу нужен не бой, а напоминание о тепле. Ты становишься "
                    "тем, кто умеет успокаивать даже изнанку."
                ),
                epilogue="Робин дарит тебе плейлист, который спасёт ещё не раз.",
            ),
        }

    def _format_game_node(self, node: GameNode) -> str:
        parts = [node.text]
        if node.options:
            parts.append("")
            for option in node.options:
                parts.append(f"{option.key}. {option.description}")
        else:
            parts.append("(Дальше только твой выбор и его последствия.)")
        return "\n".join(parts)


__all__ = ["StrangerThingsFarewell"]
