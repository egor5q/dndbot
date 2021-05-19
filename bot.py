import random
import traceback
from telebot import types, TeleBot
import time
import threading

import config
dnd = TeleBot(config.dndbot_token)
db2 = config.mongo_client.dnd
users2 = db2.users
users = db2.users
nowid = db2.nowid
spells = db2.spells
open_objects = db2.open_objects
if open_objects.find_one({}) == None:
    open_objects.insert_one({'units':{}, 'spells':{}, 'weapons':{}})
#if 'barbarian' not in spells.find_one({}):
#    spells.update_one({}, {'$set': {'barbarian': {}, 'bard': {}, 'fighter': {}, 'wizard': {}, 'druid': {},
#                                    'cleric': {}, 'warlock': {}, 'monk': {}, 'paladin': {}, 'rogue': {}, 'ranger': {},
#                                    'sorcerer': {}}})


if nowid.find_one({}) == None:
    nowid.insert_one({'id': 1})

base = {
    'units': {},
    'alpha_access': True,
    'current_stat': None,
    'current_unit': None,
    'current_spell': None,
    'current_spellstat': None,
    'spells': {},
    'current_team':None,
    'current_game':None,
    'current_weapon':None,
    'current_weaponstat':None,
    'current_effect':None,
    'current_effectstat':None,
    'cgame':None,
    'weapons':{},
    'open_objects_access':False,
    'current_openobj':None,
    'effects':{},
    'saved_games':{},
    'current_condition':None,
    'current_obj':None,
    'current_obj_to_effect': None
}

classes = ['bard', 'barbarian', 'fighter', 'wizard', 'druid', 'cleric', 'warlock', 'monk', 'paladin',
           'rogue', 'ranger', 'sorcerer']

races = ['elf', 'human', 'tiefling', 'half-elf', 'halfling', 'half-orc', 'dwarf', 'gnome']

games = {}

# rangee: [дальность_применения, тип_цели]
# duration: 0, если мгновенное
# damage: [3, 6] = 3d6

# class Spell(lvl = 0, casttime = 1, rangee = {'distance':30, 'target_type': 'target'}, duration = 1,
#           savethrow = 'dexterity', damage = [3, 6], heal = [0, 0], actions = ['damage']):
#    def __init__(self):
#        self.lvl = lvl
#        self.casttime = casttime   # действия
#        self.range = rangee        # футы
#        self.duration = duration   # минуты
#        self.savethrow = savethrow
#        self.damage = damage
#        self.heal = heal
#        self.actions = actions
#


@dnd.message_handler(commands=['open_objects'])
def openobj(m):
    if m.from_user.id != m.chat.id:
        dnd.send_message(m.chat.id, 'Можно использовать только в личке!')
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text = 'Юниты', callback_data = 'openobj menu units'))
    kb.add(types.InlineKeyboardButton(text = 'Заклинания', callback_data = 'openobj menu spells'))
    kb.add(types.InlineKeyboardButton(text = 'Оружия', callback_data = 'openobj menu weapons'))
    dnd.send_message(m.chat.id, 'Выберите меню для просмотра.', reply_markup = kb)
    

@dnd.message_handler(commands=['start'])
def startttpt(m):
    if m.from_user.id==m.chat.id:
        dnd.send_message(m.chat.id, 'Нажмите на "/", чтобы увидеть список всплывающих команд.')

@dnd.message_handler(commands=['del_object'])
def del_obj(m):
    user = createuser2(m)
    try:
        id = m.text.split(' ')[1]
        obj = None
        for ids in user['units']:
            if ids == id:
                obj = user['units'][ids]
                t = 'units'
        for ids in user['spells']:
            if ids == id:
                obj = user['spells'][ids]
                t = 'spells'
        for ids in user['weapons']:
            if ids == id:
                obj = user['weapons'][ids]
                t = 'weapons'
                
        for ids in user['effects']:
            if ids == id:
                obj = user['effects'][ids]
                t = 'effects'
                
        if obj != None:
            users.update_one({'id':user['id']},{'$unset':{t+'.'+str(obj['id']):1}})
            dnd.send_message(m.chat.id, 'Успешно удалён объект "'+obj['name']+'"!')
        else:
            dnd.send_message(m.chat.id, 'Такого объекта у вас не существует! Для удаления оружия/скилла/юнита отправьте мне '+
                             'эту команду в следующем формате:\n/del_object id\nГде id - айди объекта.')
    except:
        dnd.send_message(m.chat.id, 'Такого объекта у вас не существует! Для удаления оружия/скилла/юнита отправьте мне '+
                             'эту команду в следующем формате:\n/del_object id\nГде id - айди объекта.')
    
@dnd.message_handler(commands=['give_access'])
def give_access(m):
    if m.from_user.id == 441399484:
      try:
        x = m.text.split(' ')
        if len(x) > 1:
            if users2.find_one({'id': int(x[1])}) != None:
                users2.update_one({'id': int(x[1])}, {'$set': {'alpha_access': True}})
                dnd.send_message(m.chat.id, 'Доступ открыт.')
        elif m.reply_to_message != None:
            id = m.reply_to_message.from_user.id
            if users2.find_one({'id': id}) != None:
                users2.update_one({'id': id}, {'$set': {'alpha_access': True}})
                dnd.send_message(m.chat.id, 'Доступ открыт.')
      except:
        pass

@dnd.message_handler(commands=['addspell'])
def addspell(m):
    user = createuser2(m)
    if not user['alpha_access']:
        dnd.send_message(m.chat.id, 'У вас нет альфа-доступа! Пишите @Loshadkin.')
        return
    if len(user['spells']) > 50:
        dnd.send_message(m.chat.id, 'Максимальное число заклинаний - 50!')
        return
    spell = createspell()
    users2.update_one({'id': user['id']}, {'$set': {'spells.' + str(spell['id']): spell}})
    dnd.send_message(m.chat.id, 'Вы успешно создали заклинание! Теперь настройте его (/set_spell).')


@dnd.message_handler(commands=['create_unit'])
def createunit(m):
    user = createuser2(m)
    if not user['alpha_access']:
        dnd.send_message(m.chat.id, 'У вас нет альфа-доступа! Пишите @Loshadkin.')
        return
    if len(user['units']) > 50:
        dnd.send_message(m.chat.id, 'Максимальное число юнитов - 50!')
        return
    unit = createunit(user)
    users2.update_one({'id': user['id']}, {'$set': {'units.' + str(unit['id']): unit}})
    dnd.send_message(m.chat.id, 'Вы успешно создали юнита! Теперь настройте его (/set_stats).')
    
    
@dnd.message_handler(commands=['create_effect'])
def createeffect(m):
    user = createuser2(m)
    if not user['alpha_access']:
        dnd.send_message(m.chat.id, 'У вас нет альфа-доступа! Пишите @Loshadkin.')
        return
    if len(user['effects']) > 50:
        dnd.send_message(m.chat.id, 'Максимальное число эффектов - 50!')
        return
    effect = createeffect()
    users2.update_one({'id': user['id']}, {'$set': {'effects.' + str(effect['id']): effect}})
    dnd.send_message(m.chat.id, 'Вы успешно создали эффект! Теперь настройте его (/set_effect).')
    
    
@dnd.message_handler(commands=['set_effect'])
def set_effectt(m):
    if m.chat.id != m.from_user.id:
        dnd.send_message(m.chat.id, 'Можно использовать только в личке!')
        return
    user = createuser2(m)
    if not user['alpha_access']:
        dnd.send_message(m.chat.id, 'У вас нет альфа-доступа! Пишите @Loshadkin.')
        return
    kbs = []
    kb = types.InlineKeyboardMarkup()
    for ids in user['effects']:
        effect = user['effects'][ids]
        kbs.append(types.InlineKeyboardButton(text=effect['name'], callback_data=str(effect['id']) + ' effect_manage'))
    kb = kb_sort(kbs)
    dnd.send_message(m.chat.id, 'Выберите эффект, который хотите отредактировать.', reply_markup=kb)

    
@dnd.message_handler(commands=['create_weapon'])
def createweapon(m):
    user = createuser2(m)
    if not user['alpha_access']:
        dnd.send_message(m.chat.id, 'У вас нет альфа-доступа! Пишите @Loshadkin.')
        return
    if len(user['units']) > 50:
        dnd.send_message(m.chat.id, 'Максимальное число орудий - 50!')
        return
    weapon = createweapon()
    users2.update_one({'id': user['id']}, {'$set': {'weapons.' + str(weapon['id']): weapon}})
    dnd.send_message(m.chat.id, 'Вы успешно создали оружие! Теперь настройте его (/set_weapon_stats).')

    

@dnd.message_handler(commands=['set_stats'])
def set_stats(m):
    if m.chat.id != m.from_user.id:
        dnd.send_message(m.chat.id, 'Можно использовать только в личке!')
        return
    user = createuser2(m)
    if not user['alpha_access']:
        dnd.send_message(m.chat.id, 'У вас нет альфа-доступа! Пишите @Loshadkin.')
        return
    kbs = []
    kb = types.InlineKeyboardMarkup()
    for ids in user['units']:
        unit = user['units'][ids]
        kbs.append(types.InlineKeyboardButton(text=unit['name'], callback_data=str(unit['id']) + ' edit'))
    kb = kb_sort(kbs)
    dnd.send_message(m.chat.id, 'Выберите юнита, которого хотите отредактировать.', reply_markup=kb)
   

@dnd.message_handler(commands=['set_weapon_stats'])
def set_statsw(m):
    if m.chat.id != m.from_user.id:
        dnd.send_message(m.chat.id, 'Можно использовать только в личке!')
        return
    user = createuser2(m)
    if not user['alpha_access']:
        dnd.send_message(m.chat.id, 'У вас нет альфа-доступа! Пишите @Loshadkin.')
        return
    kbs = []
    kb = types.InlineKeyboardMarkup()
    for ids in user['weapons']:
        weapon = user['weapons'][ids]
        kbs.append(types.InlineKeyboardButton(text=weapon['name'], callback_data=str(weapon['id']) + ' weapon_manage'))
    kb = kb_sort(kbs)
    dnd.send_message(m.chat.id, 'Выберите оружие, которое хотите отредактировать.', reply_markup=kb)


@dnd.message_handler(commands=['set_spell'])
def set_stats(m):
    if m.chat.id != m.from_user.id:
        dnd.send_message(m.chat.id, 'Можно использовать только в личке!')
        return
    user = createuser2(m)
    if not user['alpha_access']:
        dnd.send_message(m.chat.id, 'У вас нет альфа-доступа! Пишите @Loshadkin.')
        return
    kbs = []
    kb = types.InlineKeyboardMarkup()
    for ids in user['spells']:
        spell = user['spells'][ids]
        kbs.append(types.InlineKeyboardButton(text=spell['name'], callback_data=str(spell['id']) + ' spell_manage'))
    kb = kb_sort(kbs)
    dnd.send_message(m.chat.id, 'Выберите спелл, который хотите отредактировать.', reply_markup=kb)


@dnd.message_handler(content_types=['photo'])
def msgsp(m):
    user = createuser2(m)
    if user['current_stat'] != None and user['current_unit'] != None and m.from_user.id == m.chat.id:
        unit = user['units'][str(user['current_unit'])]
        if user['current_stat'] == 'photo':
            users2.update_one({'id': user['id']}, {
                '$set': {'units.' + str(user['current_unit']) + '.' + user['current_stat']: m.photo[0].file_id}})
            user = createuser2(m)
            unit = user['units'][str(user['current_unit'])]
            users2.update_one({'id': user['id']}, {'$set': {'current_stat': None, 'current_unit': None}})
            dnd.send_message(m.chat.id, 'Новое фото установлено!')
            sendunitedit(m.chat.id, unit)


@dnd.message_handler(commands=['create_map'])
def mapp(m):
    if m.chat.id not in games:
        x = m.text.split(' ')
        teams = 2
        if len(x)>1:
            try:
                teams = int(x[1])
            except:
                pass
        if teams < 2:
            teams = 2
        games.update(creategame(m))
        kb=types.InlineKeyboardMarkup()
        i=1
        while i <= teams: 
            kb.add(types.InlineKeyboardButton(text = 'Добавить в команду '+str(i), callback_data = 'addt '+str(i)+' '+str(m.chat.id)))
            i+=1
        dnd.send_message(m.chat.id, 'Игра была создана! Теперь Мастер должен добавить в неё персонажей.', reply_markup=kb)
    
   
@dnd.message_handler(commands=['start_map'])
def startmap(m):
    if m.chat.id in games:
        user = createuser2(m)
        game = games[m.chat.id]
        if m.from_user.id != game['master']['id']:
            dnd.send_message(m.chat.id, 'Только Мастер может запустить игру!')
            return
        if game['started'] == True:
            dnd.send_message(m.chat.id, 'Игра уже идёт!')
            return
        game['started'] = True
        text = ''
        for ids in game['units']:
            unit = game['units'][ids]
            min = 1
            max = 20
            x = random.randint(min,max)
            unit.update({'initiative': x})
            text += 'Инициатива '+unit['name']+': ('+str(min)+'d'+str(max)+') = '+str(x)+'\n'
        dnd.send_message(m.chat.id, text)
        text = 'Очерёдность ходов:\n'
        time.sleep(4)
        turned = []
        while len(turned) < len(game['units']):
            i = -10
            nowu = None
            for ids in game['units']:
                unit = game['units'][ids]
                if unit['id'] not in turned:
                    if unit['initiative'] >= i:
                        nowu = unit
                        i = unit['initiative']
            if nowu != None:
                turned.append(nowu['id'])
                nowu.update({'turn':len(turned)})
                text += str(len(turned))+'й: '+nowu['name']+'\n'
        dnd.send_message(m.chat.id, text)
        for ids in game['units']:
            game['units'][ids].update({'alive':True,
                                      'current_act':None,
                                      'speech_wait':False,
                                      'speeched':False,
                                      'freeatk':1,
                                      'done_turn':False,
                                      'stunned':0})
            
        for ids in game['units']:
            n = False
            weapon = game['units'][ids]['current_weapon']
            try:
                weapon['downloaded']
            except:
                n = True
            if n:
                if weapon != None:
                    try:
                        game['units'][ids]['current_weapon'] = user['weapons'][str(weapon['id'])]
                    except:
                        pass
        sp = []
        un1 = []
        dp = []          
        for ids in game['units']:
            n = False
            unit = game['units'][ids]
            for idss in unit['spells']:
                spell = unit['spells'][idss]
                try:
                    spell['downloaded']
                except:
                    n = True
                if n:
                    try:
                        sp.append(idss)
                        un1.append(ids)
                        try:
                            dp.append(user['spells'][str(spell['id'])])
                        except:
                            dp.append(user['spells'][spell['id']])
                       
                    except:
                        dnd.send_message(441399484, traceback.format_exc())
        i = 0
        for ids in dp:
            game['units'][un1[i]]['spells'][sp[i]] = ids
            i += 1
            
        for ids in game['units']:
            if game['units'][ids]['current_weapon'] == None:
                game['units'][ids]['current_weapon'] = {
                                            'id':randomid(),
                                            'name':'Кулак',
                                            'maxdmg':2,
                                            'mindmg':1,
                                            'dmg_buff':0,
                                            'accuracy_buff':0
                                            }
        teams = {}
        for ids in game['units']:
            unit = game['units'][ids]
            if unit['team'] not in teams:
                pc = poscodegen(key = 'position_code', d = teams)
                teams.update({unit['team']:{'team':unit['team'], 'position_code':pc}})
                print(pc)
                unit.update({'position_code':pc})
            else:
                unit.update({'position_code': teams[unit['team']]['position_code']})
                
        next_turn(game)
                    
            
def poscodegen(key = None, d = None, game = None):
    if d == None and game == None:
        return
    cods = []
    x = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
    if d != None:
        for ids in d:
            cods.append(d[ids][key])
    elif game != None:
        for ids in game['units']:
            cods.append(game['units'][ids]['position_code'])
    code = ''
    while len(code) < 4:
        code += random.choice(x)
    while code in cods:
        code = ''
        while len(code) < 4:
            code += random.choice(x)
    return code
    
            
        
            
def uuu():
    return {
        'id': 0,
        'name': 0,
        'class': 0,
        'race': 0,
        'hp': 0,
        'maxhp':0,
        'strenght': 0,
        'dexterity': 0,
        'constitution': 0,
        'intelligence': 0,
        'wisdom': 0,
        'charisma': 0,
        'armor_class': random.randint(8, 16),
        'initiative': 10,
        'speed': 30,
        'photo': None,
        'death_saves(success)': 0,
        'death_saves(fail)': 0,
        'spells': {},
        'inventory': [],
        'current_weapon': None,
        'owner': id,
        'player': None,
        'max_spells':{},
        'alive':True,
        'freeatk':1
    }


    
            
@dnd.message_handler(commands=['delete'])
def dell(m):
    if m.chat.id in games:
        game = games[m.chat.id]
        user = dnd.get_chat_member(m.chat.id, m.from_user.id)
        admins = ['administrator', 'creator']
        if m.from_user.id == game['master']['id'] or user.status in admins:
            try:
                game['ctimer'].cancel()
            except:
                dnd.send_message(441399484, traceback.format_exc())
            del games[game['id']]
            game['kill'] = True
            dnd.send_message(m.chat.id, 'Игра удалена.')
            
            
            
@dnd.message_handler()
def msgs(m):
  try:
    user = createuser2(m)
    
    if user['cgame'] != None:
        try:
            game = games[user['cgame']]
            for ids in game['units']:
                if game['units'][ids]['speech_wait']:
                    say_speech(game['units'][ids], game, m.text)
                    kb = mainmenu(game, unit)
                    dnd.send_message(unit['player'], 'Выберите действие персонажа '+unit['name']+'.', reply_markup=kb)
        except:
            pass
    
    if user['current_stat'] != None and user['current_unit'] != None and m.from_user.id == m.chat.id:
        try:
            unit = user['units'][str(user['current_unit'])]
        except:
            return
        numbervalues = ['hp', 'maxhp', 'strenght', 'dexterity', 'constitution', 'intelligence',
                        'wisdom', 'charisma', 'armor_class', 'speed', 'current_weapon']
        blist = ['inventory', 'spells', 'photo', 'addcast', 'max_spells']
        if user['current_stat'] not in blist:
            test = False
            if user['current_stat'] in numbervalues:
                test = True
            val = m.text
            if test:
                try:
                    val = int(m.text)
                except:
                    dnd.send_message(m.chat.id, 'Нужно значение типа int!')
                    return
            if user['current_stat'] != 'player' and user['current_stat'] != 'current_weapon':
                users2.update_one({'id': user['id']},
                              {'$set': {'units.' + str(user['current_unit']) + '.' + user['current_stat']: val}})
            elif user['current_stat'] == 'player':
                try:
                    users2.update_one({'id': user['id']},
                              {'$set': {'units.' + str(user['current_unit']) + '.' + user['current_stat']: int(val)}})
                except:
                    dnd.send_message(m.chat.id, 'Неверный формат! Пришлите мне айди игрока!')
                    return
            elif user['current_stat'] == 'current_weapon':
                try:
                    weapon = user['weapons'][m.text]
                    users2.update_one({'id': user['id']},
                              {'$set': {'units.' + str(user['current_unit']) + '.' + user['current_stat']: weapon}})
                except:
                    dnd.send_message(m.chat.id, 'Неверный формат! Пришлите мне айди оружия!')
                    return
                
            user = createuser2(m)
            unit = user['units'][str(user['current_unit'])]
            users2.update_one({'id': user['id']}, {'$set': {'current_stat': None, 'current_unit': None}})
            dnd.send_message(m.chat.id, unit['name'] + ': успешно изменена характеристика "' + user[
                'current_stat'] + '" на "' + str(val) + '"!')
            sendunitedit(m.chat.id, unit)

        else:
            if user['current_stat'] == 'inventory':
                inv = []
                t = m.text.split(', ')
                for ids in t:
                    inv.append(ids)
                tt = ''
                for ids in inv:
                    tt += ids + ', '
                tt = tt[:len(tt) - 2]
                users2.update_one({'id': user['id']},
                                  {'$set': {'units.' + str(user['current_unit']) + '.' + user['current_stat']: inv}})
                user = createuser2(m)
                unit = user['units'][str(user['current_unit'])]
                users2.update_one({'id': user['id']}, {'$set': {'current_stat': None, 'current_unit': None}})
                dnd.send_message(m.chat.id, unit['name'] + ': инвентарь юнита успешно изменён на ' + tt + '!')
                sendunitedit(m.chat.id, unit)
            elif user['current_stat'] == 'addcast':
                try:
                    spell = user['spells'][m.text]
                except:
                    dnd.send_message(m.chat.id, 'Такого спелла не существует!')
                    users2.update_one({'id': user['id']}, {'$set': {'current_stat': None, 'current_unit': None}})
                    return
                users.update_one({'id':user['id']},{'$set':{'units.'+str(user['current_unit'])+'.spells.'+str(spell['id']):spell}})
                dnd.send_message(m.chat.id, 'Заклинание "'+spell['name']+'" успешно добавлено к юниту!')
                users2.update_one({'id': user['id']}, {'$set': {'current_stat': None, 'current_unit': None}})
                sendunitedit(m.chat.id, unit)
                
            elif user['current_stat'] == 'max_spells':
                try:
                    er = 'Ошибки:\n'
                    succ = ''
                    d = {}
                    t = m.text.split(' ')
                    for ids in t:
                        lvl = ids.split(':')[0]
                        val = ids.split(':')[1]
                        try:
                            d.update({lvl:int(val)})
                            succ += lvl+' лвл: '+str(val)+' заклинаний\n'
                        except:
                            if val == "inf":
                                d.update({lvl:val})
                                succ += lvl+' лвл: '+str(val)+' заклинаний\n'
                            else:
                                er += 'Неверный параметр значения заклинания уровня '+lvl+'!\n'
                    for ids in d:
                        users.update_one({'id':user['id']},{'$set':{'units.'+str(unit['id'])+'.max_spells.'+ids:d[ids]}})
                    users2.update_one({'id': user['id']}, {'$set': {'current_stat': None, 'current_unit': None}})
                    dnd.send_message(m.chat.id, 'Успешно установленные значения:\n'+succ+'\n'+er)
                    sendunitedit(m.chat.id, unit) 
                except:
                    dnd.send_message(m.chat.id, 'Неверный формат!')
                
                    

    elif user['current_spell'] != None and user['current_spellstat'] != None and m.from_user.id == m.chat.id:
        val = m.text
        attributes = ['strenght', 'dexterity', 'wisdom', 'charisma', 'constitution', 'intelligence']
        try:
            spell = user['spells'][str(user['current_spell'])]
        except:
            dnd.send_message(441399484, traceback.format_exc())
            return
        r = False
        numbervalues = ['damage', 'heal']
        targettypes = ['all_enemy', 'all_ally', 'enemy', 'ally', 'self', 'all', 'ally!self', 'all_ally!self', 'all!self', 'any', 'any!self']
        damagetypes = ['target', 'aoe']
        test1 = False      
        if user['current_spellstat'] == 'savethrow':
            st = spell['savethrow']
            text = m.text.lower()
            if 'аттрибут' in m.text.lower():
                val = text.split('аттрибут')[1]
                val = val.split(':')[1]
                if val[0] == ' ':
                    val = val[1:]
                    print(val)
                val = val.split(' ')[0]
                if val not in attributes:
                    tt = ''
                    for ids in attributes:
                        tt += '`'+ids+'` '
                    dnd.send_message(m.chat.id, 'Необходимо выставить одно из следующих значений:\n'+tt, parse_mode = 'markdown')
                    return
                else:
                    users2.update_one({'id': user['id']},
                          {'$set': {'spells.' + str(user['current_spell']) + '.savethrow.attribute': val}})
                    dnd.send_message(m.chat.id, 'Успешно изменено значение "аттрибут" на '+str(val)+'!')
                    r = True
            if 'сложность' in m.text.lower():
                val = text.split('сложность')[1]
                val = val.split(':')[1]
                if val[0] == ' ':
                    val = val[1:]
                    print(val)
                val = val.split(' ')[0]
                try:
                    val = int(val)
                except:
                    dnd.send_message(m.chat.id, 'Необходимо значение типа int!')
                    return
                users2.update_one({'id': user['id']},
                          {'$set': {'spells.' + str(user['current_spell']) + '.savethrow.value': val}})
                dnd.send_message(m.chat.id, 'Успешно изменено значение "сложность" на '+str(val)+'!')
                r = True
            if r:
                user = createuser2(m)
                spell = user['spells'][str(user['current_spell'])]
                users2.update_one({'id': user['id']}, {'$set': {'current_spellstat': None, 'current_spell': None}})
                sendspelledit(m.chat.id, spell)
                return
            
        elif user['current_spellstat'] == 'target_type':
            test1 = True
        if test1:
            val = m.text.lower()
            if val not in targettypes:
                tt = ''
                for ids in targettypes:
                    tt += '`'+ids+'` '
                dnd.send_message(m.chat.id, 'Необходимо выставить одно из следующих значений:\n'+tt, parse_mode='markdown')
                return
        if user['current_spellstat'] == 'damage_type':
            val = m.text.lower()
            if val not in damagetypes:
                tt = ''
                for ids in damagetypes:
                    tt += '`'+ids+'` '
                dnd.send_message(m.chat.id, 'Необходимо выставить одно из следующих значений:\n'+tt, parse_mode='markdown')
                return
            
        test2 = False    
        if user['current_spellstat'] in numbervalues:
            test2 = True
        if test2:
            try:
                val = int(m.text)
            except:
                if 'd' in m.text:
                    try:
                        a = m.text.split('d')
                        int(a[0])
                        int(a[1])
                    except:
                        dnd.send_message(m.chat.id, 'Нужно значение типа int, если оно статичное, или формат значения "XdY", '+
                                         'где X - количество кидаемых кубов, а Y - максимальное значение каждого куба. Пример: 1d6 - '+
                                        'будет выпадать случайное значение от 1 до 6.')
                        return
                else:
                    dnd.send_message(m.chat.id, 'Нужно значение типа int, если оно статичное, или формат значения "XdY", '+
                                         'где X - количество кидаемых кубов, а Y - максимальное значение каждого куба. Пример: 1d6 - '+
                                        'будет выпадать случайное значение от 1 до 6.')
                    return
        
        users2.update_one({'id': user['id']},
                          {'$set': {'spells.' + str(user['current_spell']) + '.' + user['current_spellstat']: val}})
        user = createuser2(m)
        spell = user['spells'][str(user['current_spell'])]
        users2.update_one({'id': user['id']}, {'$set': {'current_spellstat': None, 'current_spell': None}})
        dnd.send_message(m.chat.id, spell['name'] + ': успешно изменена характеристика "' + user[
            'current_spellstat'] + '" на "' + str(val) + '"!')
        sendspelledit(m.chat.id, spell)
        
        
    elif user['current_weapon'] != None and user['current_weaponstat'] != None and m.from_user.id == m.chat.id:
        val = m.text
        try:
            weapon = user['weapons'][str(user['current_weapon'])]
        except:
            return
        numbervalues = ['maxdmg', 'mindmg', 'dmg_buff', 'accuracy_buff']
        test = False
        test2 = False
        if user['current_weaponstat'] == 'range':
            test2 = True
        if user['current_weaponstat'] in numbervalues:
            test = True
        val = m.text
        if test:
            try:
                val = int(m.text)
            except:
                dnd.send_message(m.chat.id, 'Нужно значение типа int!')
                return
        if test2:
            if m.text.lower() not in ['melee', 'ranged']:
                dnd.send_message(m.chat.id, 'Нужно одно из этих значений: `melee`, `ranged`.', parse_mode = 'markdown')
                return
            else:
                val = m.text.lower()
        users2.update_one({'id': user['id']},
                          {'$set': {'weapons.' + str(user['current_weapon']) + '.' + user['current_weaponstat']: val}})
        user = createuser2(m)
        weapon = user['weapons'][str(user['current_weapon'])]
        users2.update_one({'id': user['id']}, {'$set': {'current_weaponstat': None, 'current_weapon': None}})
        dnd.send_message(m.chat.id, weapon['name'] + ': успешно изменена характеристика "' + user[
            'current_weaponstat'] + '" на "' + str(val) + '"!')
        sendweaponedit(m.chat.id, weapon)
        
    elif user['current_openobj'] != None:
        co = user['current_openobj']
        try:
            obj = user[co][m.text]
        except:
            dnd.send_message(m.chat.id, 'Такого объекта ('+co+') у вас не существует! Отменяю добавление.')
            users2.update_one({'id': user['id']}, {'$set': {'current_openobj': None}})
            return
        if len(open_objects.find_one({})[co]) >= 75:
            dnd.send_message(m.chat.id, 'Лимит объектов общего доступа - 75! Пишите @Loshadkin.')
            return
        open_objects.update_one({},{'$set':{co+'.'+str(obj['id']):obj}})
        dnd.send_message(m.chat.id, 'Объект ('+co+') ('+obj['name']+') успешно добавлен в общий доступ!')
        users2.update_one({'id': user['id']}, {'$set': {'current_openobj': None}})
        
    elif user['current_obj'] != None and user['current_condition'] != None:
        allow = []
        nxt = False
        err = ''
        txt = ''
        if user['current_condition'] == 'target_stats' or user['current_condition'] == 'unit_stats':
            unit = uuu()
            x = m.text.split(' ')
            sl = {}
            for ids in x:
                try:
                    param = ids.split(':')[0]
                    if param in unit:
                        value = ids.split(':')[1]
                        sl.update({param:value})
                        txt += 'Успешно изменен параметр "'+param+'" на "'+value+'"!\n'
                    else:
                        err += 'Ошибка в добавлении '+ids+': параметра "'+param+'" у юнита не существует!\n'
                except:
                    err += 'Ошибка в добавлении '+ids+'!\n'
            
            for ids in sl:
                users.update_one({'id':user['id']},{'$set':{'effects.'+user['current_obj']+'.condition.'+user['current_condition']+'.'+ids:sl[ids]}})
            if txt == '':
                txt = 'Не удалось выставить ни одного параметра!'
            if err != '':
                txt += '\n\nОшибки:\n'+err
            users.update_one({'id':user['id']},{'$set':{'current_condition':None, 'current_obj':None}})
            dnd.send_message(m.chat.id, txt)
            
        elif user['current_condition'] == 'chance':
            users.update_one({'id':user['id']},{'$set':{'effects.'+user['current_obj']+'.condition.'+user['current_condition']:m.text}})
            users.update_one({'id':user['id']},{'$set':{'current_condition':None, 'current_obj':None}})
            dnd.send_message(m.chat.id, 'Успешно изменено значение параметра "chance" на "'+m.text+'"!')
            
    elif user['current_effect'] != None and user['current_effectstat'] != None:
        try:
            x = m.text
            if user['current_effectstat'] == 'duration':
                try:
                    x = int(m.text)
                except:
                    dnd.send_message(m.chat.id, 'Требуется значение типа int!')
                    return
            if user['current_effectstat'] == 'effect':
                allow = ['stun', 'weakness', 'kill', 'mark', 'bonus_accuracy', 'bonus_strenght', 'bonus_dexterity', 'bonus_wisdom', 
                  'bonus_charisma', 'bonus_constitution', 'bonus_intelligence', 'bonus_armor', 'bonus_maxhp', 'bonus_hp', 'crit']
                if m.text not in allow:
                    dt = ''
                    for ids in allow:
                        dt += '`'+ids.replace('_', '_')+'` '
                    dnd.send_message(m.chat.id, 'Для выставления "'+user['current_effectstat']+'" требуется одно из следующих значений:\n'+
                                     dt, parse_mode='markdown')
                    return
            if user['current_effectstat'] == 'target':
                allow = ['target', 'unit']
                if m.text not in allow:
                    dt = ''
                    for ids in allow:
                        dt += '`'+ids.replace('_', '_')+'` '
                    dnd.send_message(m.chat.id, 'Для выставления "'+user['current_effectstat']+'" требуется одно из следующих значений:\n'+
                                     dt, parse_mode='markdown')
                    return
            users.update_one({'id':user['id']},{'$set':{'effects.'+str(user['current_effect'])+'.'+str(user['current_effectstat']):x}})
            users.update_one({'id':user['id']},{'$set':{'current_effect':None, 'current_effectstat':None}})
            dnd.send_message(m.chat.id, 'Успешно изменён параметр эффекта "'+user['current_effectstat']+'" на "'+m.text+'"!')
        except:
            users.update_one({'id':user['id']},{'$set':{'current_effect':None, 'current_effectstat':None}})
            dnd.send_message(441399484, traceback.format_exc())
        
    elif user['current_obj_to_effect'] != None:
        try:
            effect = user['effects'][m.text]
        except:
            dnd.send_message(m.chat.id, 'Такого эффекта не существует! Отменяю добавление.')
            users.update_one({'id':user['id']},{'$set':{'current_obj_to_effect':None}})
            return
        try:
            obj = user['spells'][str(user['current_obj_to_effect'])]
            w = 'spells'
        except:
            try:
                obj = user['weapons'][str(user['current_obj_to_effect'])]
                w = 'weapons'
            except:
                dnd.send_message(441399484, str(user['current_obj_to_effect']))
                dnd.send_message(m.chat.id, 'Ошибка! Отменяю добавление эффекта.')
                users.update_one({'id':user['id']},{'$set':{'current_obj_to_effect':None}})
                return
        users.update_one({'id':user['id']},{'$set':{w+'.'+str(obj['id'])+'.effects.'+str(effect['id']):effect}})
        dnd.send_message(m.chat.id, 'Эффект успешно добавлен!')
        users.update_one({'id':user['id']},{'$set':{'current_obj_to_effect':None}})
        
    elif user['current_game'] != None and user['current_team'] != None:
        try:
            unit = int(m.text)
        except:
            return
        cunit = None
        for ids in user['units']:
            if user['units'][ids]['id'] == unit:
                cunit = user['units'][ids]
        if cunit == None:
            dnd.send_message(m.chat.id, 'Такого юнита у вас не существует!')
            return
        try:
            games[user['current_game']]['units'].update({cunit['id']:cunit})
            u = games[user['current_game']]['units'][cunit['id']]
            u.update({'team':user['current_team']})
            dnd.send_message(m.chat.id, 'Юнит '+cunit['name']+' успешно добавлен в команду '+user['current_team']+'!')
            users.update_one({'id':user['id']},{'$set':{'current_game':None, 'current_team':None}})
        except:
            dnd.send_message(441399484, traceback.format_exc())
            dnd.send_message(m.chat.id, 'Игры не существует! Отменяю добавление юнита.')
            users.update_one({'id':user['id']},{'$set':{'current_game':None, 'current_team':None}})
  except:
    print(traceback.format_exc())
    dnd.send_message(m.chat.id, 'error!')
    


@dnd.callback_query_handler(func=lambda call: True)
def inline(call):
  try:
    user = createuser2(call)
    if 'edit' in call.data:
        try:
            unit = user['units'][call.data.split(' ')[0]]
        except:
            dnd.answer_callback_query(call.id, 'Такого юнита не существует!', show_alert=True)
            return
        kb = create_edit_kb(unit)
        dnd.send_message(call.message.chat.id, 'Нажмите на характеристику для её изменения.', reply_markup=kb)
       
    elif 'openobj' in call.data:
        objs = open_objects.find_one({})
        act = call.data.split(' ')[1]
        if act == 'menu':
            what = call.data.split(' ')[2]
            if what == 'weapons':
                t = 'оружие'
            elif what == 'spells':
                t = 'заклинание'
            elif what == 'units':
                t = 'юнита'
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text = 'Добавить '+t, callback_data = 'openobj add '+what))
            kb.add(types.InlineKeyboardButton(text = 'Загрузить '+t, callback_data = 'openobj load '+what))
            kb.add(types.InlineKeyboardButton(text = 'Главное меню', callback_data = 'openobj mainmenu'))
            medit('Выберите действие.', call.message.chat.id, call.message.message_id, reply_markup = kb)
            
        elif act == 'load':
            what = call.data.split(' ')[2]
            kb = types.InlineKeyboardMarkup()
            kbs = []
            kb = types.InlineKeyboardMarkup()
            for ids in objs[what]:
                obj = objs[what][ids]
                kbs.append(types.InlineKeyboardButton(text = obj['name'], callback_data = 'openobj download '+what+' '+str(obj['id'])))
            kb = kb_sort(kbs)
            kb.add(types.InlineKeyboardButton(text = 'Главное меню', callback_data = 'openobj mainmenu'))
            medit('Выберите обьект для загрузки.', call.message.chat.id, call.message.message_id, reply_markup = kb)
            
        elif act == 'add':
            what = call.data.split(' ')[2]
            if what == 'weapons':
                t = 'оружия'
            elif what == 'spells':
                t = 'заклинания'
            elif what == 'units':
                t = 'юнита'
            users.update_one({'id':call.from_user.id},{'$set':{'current_openobj':what}})
            dnd.send_message(call.message.chat.id, 'Теперь пришлите мне id '+t+', которого хотите добавить в публичный доступ.')
            
        elif act == 'download':
            what = call.data.split(' ')[2]
            obj = objs[what][call.data.split(' ')[3]]
            if what == 'units':
                newobj = createunit(userid = call.from_user.id)  
            elif what == 'weapons':
                newobj = createweapon() 
            elif what == 'spells':
                newobj = createspell() 
                
            for ids in obj:
                if ids != 'id' and ids != 'owner':
                    newobj[ids] = obj[ids]
            try:
                for ids in newobj['spells']:
                    newobj['spells'][ids].update({'downloaded':True})
            except:
                pass
            try:
                newobj['current_weapon'].update({'downloaded':True})
            except:
                pass
            if len(user[what]) >= 50:
                medit('Максимальное число объектов одного типа - 50!', call.message.chat.id, call.message.message_id)
                return
            users.update_one({'id': user['id']}, {'$set': {what+'.' + str(newobj['id']): newobj}})
            medit('Объект "'+newobj['name']+'" успешно добавлен к вам в коллекцию!', call.message.chat.id, call.message.message_id)
            
        elif act == 'mainmenu':
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text = 'Юниты', callback_data = 'openobj menu units'))
            kb.add(types.InlineKeyboardButton(text = 'Заклинания', callback_data = 'openobj menu spells'))
            kb.add(types.InlineKeyboardButton(text = 'Оружия', callback_data = 'openobj menu weapons'))
            medit('Выберите меню для просмотра.', call.message.chat.id, call.message.message_id, reply_markup = kb)
            
                
            
    
    elif 'addcast' in call.data or 'delcast' in call.data:
        unit = user['units'][call.data.split(' ')[1]]
        what = call.data.split(' ')[0]
        txt = ' Список текущих заклинаний:\n'
        for ids in unit['spells']:
            spel = unit['spells'][ids]
            txt += spel['name']+': '+str(spel['lvl'])+' лвл\n'
        if what == 'addcast':
            users2.update_one({'id': user['id']}, {'$set': {'current_unit': unit['id'], 'current_stat': what}})  
            dnd.send_message(call.message.chat.id, 'Теперь пришлите мне ID заклинания, которое хотите добавить.'+txt)
        elif what == 'delcast':
            kb = types.InlineKeyboardMarkup()
            for ids in user['units'][str(unit['id'])]['spells']:
                spell = user['units'][str(unit['id'])]['spells'][ids]
                kb.add(types.InlineKeyboardButton(text = spell['name'], callback_data = 'delete_spell '+str(unit['id'])+' '+str(spell['id'])))
            medit('Нажмите на спелл для его удаления.', call.message.chat.id, call.message.message_id, reply_markup = kb)
            
    elif 'addeffect' in call.data or 'deleffect' in call.data:
        try:
            obj = user['spells'][call.data.split(' ')[1]]
            w = 'spells'
        except:
            try:
                obj = user['weapons'][call.data.split(' ')[1]]
                w = 'weapons'
            except:
                dnd.answer_callback_query(call.id, 'Обьекта не существует!')
                return
        
        what = call.data.split(' ')[0]
        txt = ' Список текущих эффектов:\n'
        for ids in obj['effects']:
            ef = obj['effects'][ids]
            txt += ef['name']+'\n'
        if what == 'addeffect':
            users2.update_one({'id': user['id']}, {'$set': {'current_obj_to_effect': obj['id']}})  
            dnd.send_message(call.message.chat.id, 'Теперь пришлите мне ID эффекта, который хотите добавить.'+txt)
        elif what == 'deleffect':
            kb = types.InlineKeyboardMarkup()
            for ids in user[w][str(obj['id'])]['effects']:
                ef = user[w][str(obj['id'])]['effects'][ids]
                kb.add(types.InlineKeyboardButton(text = ef['name'], callback_data = 'delete_effect '+str(ef['id'])+' '+str(obj['id'])))
            medit('Нажмите на эффект для его удаления.', call.message.chat.id, call.message.message_id, reply_markup = kb)
            
            
    elif 'delete_spell' in call.data:
        unit = user['units'][call.data.split(' ')[1]]
        if call.data.split(' ')[2] in unit['spells']:
            users.update_one({'id':user['id']},{'$unset':{'units.'+str(unit['id'])+'.spells.'+call.data.split(' ')[2]: 1}})
            medit('Спелл удалён!', call.message.chat.id, call.message.message_id)
            sendunitedit(call.message.chat.id, unit)
            
    elif 'delete_effect' in call.data:
        try:
            obj = user['spells'][call.data.split(' ')[2]]
            w = 'spells'
        except:
            try:
                obj = user['weapons'][call.data.split(' ')[2]]
                w = 'weapons'
            except:
                dnd.answer_callback_query(call.id, 'Обьекта не существует!')
                return
            
        if call.data.split(' ')[1] in obj['effects']:
            users.update_one({'id':user['id']},{'$unset':{w+'.'+str(obj['id'])+'.effects.'+call.data.split(' ')[1]: 1}})
            medit('Эффект удалён!', call.message.chat.id, call.message.message_id)

    elif 'change' in call.data and 'spell_change' not in call.data and 'weapon_ch' not in call.data and 'spell_manage' not in call.data:
        blist = ['inventory', 'spells', 'photo', 'max_spells']
        numbervalues = ['hp', 'maxhp', 'strenght', 'dexterity', 'constitution', 'intelligence',
                        'wisdom', 'charisma', 'armor_class', 'speed', 'name', 'player', 'current_weapon']
        what = call.data.split(' ')[1]
        try:
            unit = user['units'][call.data.split(' ')[2]]
        except:
            dnd.answer_callback_query(call.id, 'Такого юнита не существует!', show_alert=True)
            return
        users2.update_one({'id': user['id']}, {'$set': {'current_unit': unit['id'], 'current_stat': what}})
        if what not in blist:
            tt = ''
            if what in numbervalues:
                if what == 'current_weapon':
                    tt += ' Требуется айди оружия!'
                dnd.send_message(call.message.chat.id,
                                 'Теперь пришлите мне новое значение характеристики "' + what + '".'+tt)
            else:
                if what == 'race':
                    r = 'расы'
                    alls = ''
                    for ids in races:
                        alls += '`' + ids + '` '
                elif what == 'class':
                    r = 'классы'
                    alls = ''
                    for ids in classes:
                        alls += '`' + ids + '` '
                dnd.send_message(call.message.chat.id,
                                 'Теперь пришлите мне новое значение характеристики "' + what + '".\n' +
                                 'Существующие ' + r + ': ' + alls, parse_mode='markdown')
        else:
            if what == 'inventory':
                inv = '`'
                for ids in unit['inventory']:
                    inv += ids + ', '
                inv = inv[:len(inv) - 2]
                inv += '`'
                if inv == '`':
                    inv = 'Пусто!'
                dnd.send_message(call.message.chat.id,
                                 'Теперь пришлите мне новый инвентарь, перечисляя предметы через запятую. Текущий ' +
                                 'инвентарь: ' + inv, parse_mode='markdown')
            elif what == 'photo':
                if unit['photo'] != None:
                    dnd.send_photo(call.message.chat.id, unit['photo'],
                                   caption='Текущая фотография юнита. Для изменения отправьте новое фото.')
                else:
                    dnd.send_message(call.message.chat.id,
                                     'Фотография отсутствует. Для изменения отправьте новое фото.')
                    
            elif what == 'spells':
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton(text = 'Добавить заклинание', callback_data = 'addcast '+str(unit['id'])))
                kb.add(types.InlineKeyboardButton(text = 'Удалить заклинание', callback_data = 'delcast '+str(unit['id'])))
                medit('Нажмите кнопку для изменения параметров.', call.message.chat.id, call.message.message_id, reply_markup = kb)
                
            elif what == 'max_spells':
                dnd.send_message(call.message.chat.id, 'Теперь пришлите мне значения максимума используемых за раунд заклинаний '+
                                 'в следующем формате:\n1:6 2:4 3:1\nГде первое число - уровень заклинания, а второе - '+
                                 'максимальное использование заклинаний этого уровня за битву. Чтобы снять ограничение, поставьте '+
                                 '"inf" после уровня. Перед и после двоеточия не должно быть пробелов!')
                txt = ''
                for ids in unit['max_spells']:
                    txt += ids+' уровень: '+str(unit['max_spells'][ids])+' заклинаний\n'
                if txt == '':
                    txt = 'Пусто!'
                dnd.send_message(call.message.chat.id, 'Текущие значения:\n'+txt)
                
          ################################################
    elif 'spell_change' in call.data:
        what = call.data.split(' ')[1]
        try:
            spell = user['spells'][call.data.split(' ')[2]]
        except:
            dnd.answer_callback_query(call.id, 'Такого спелла не существует!', show_alert=True)
            return
        text = ''
        if what == 'savethrow':
            text += ' Текущее значение:\n'
            text += '┞ Аттрибут: '+str(spell['savethrow']['attribute'])+'\n'
            text += '┕ Сложность: '+str(spell['savethrow']['value'])+'\n'
            text += 'Чтобы выставить новые значения (одно или несколько, через пробел), вводите их в следующем формате:\n'
            text += '`Аттрибут: значение`\n'
            text += '`Сложность: значение`\nПример: `аттрибут: dexterity сложность: 5`'
            
        if what == 'custom_text':
            text += ' Текущее значение: "'+str(spell['custom_text'])+'".\nВозможные переменные:\n{target_name} - имя цели (только '+\
            'если тип заклинания - направленное на цель);\n'+\
            '{spell_name} - название заклинания;\n{unit_name} - имя юнита.'
        text = text.replace('_', '\_')
        if what == 'effects':
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text = 'Добавить эффект', callback_data = 'addeffect '+str(spell['id'])))
            kb.add(types.InlineKeyboardButton(text = 'Удалить эффект', callback_data = 'deleffect '+str(spell['id'])))
            medit('Нажмите кнопку для изменения параметров.', call.message.chat.id, call.message.message_id, reply_markup = kb)
            return
        users2.update_one({'id': user['id']}, {'$set': {'current_spell': spell['id'], 'current_spellstat': what}})
        if what == 'classes' or what == 'description':
            text += '\nТекущее значение: "' + str(spell[what]) + '"'
        dnd.send_message(call.message.chat.id,
                         'Теперь пришлите мне новое значение характеристики заклинания "' + what.replace('_', '\_') + '".' + text, parse_mode = 'markdown')
        
    elif 'weapon_ch' in call.data:
        what = call.data.split(' ')[1]
        try:
            weapon = user['weapons'][call.data.split(' ')[2]]
        except:
            dnd.send_message(441399484, traceback.format_exc())
            dnd.answer_callback_query(call.id, 'Такого оружия не существует!', show_alert=True)
            return
        users2.update_one({'id': user['id']}, {'$set': {'current_weapon': weapon['id'], 'current_weaponstat': what}})
        text = ''
        if what == 'custom_attack_text':
            text = ' Текущее значение: "'+str(weapon['custom_attack_text'])+'".\nВозможные переменные:\n{target_name} - имя цели;\n'+\
            '{weapon_name} - название оружия;\n{unit_name} - имя юнита.'
        if what == 'effects':
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text = 'Добавить эффект', callback_data = 'addeffect '+str(weapon['id'])))
            kb.add(types.InlineKeyboardButton(text = 'Удалить эффект', callback_data = 'deleffect '+str(weapon['id'])))
            medit('Нажмите кнопку для изменения параметров.', call.message.chat.id, call.message.message_id, reply_markup = kb)
            users2.update_one({'id': user['id']}, {'$set': {'current_weapon': None, 'current_weaponstat': None}})
            return
        dnd.send_message(call.message.chat.id,
                         'Теперь пришлите мне новое значение характеристики оружия "' + what + '".' + text)
        
    elif 'effect_ch' in call.data:
        what = call.data.split(' ')[1]
        try:
            effect = user['effects'][call.data.split(' ')[2]]
        except:
            dnd.send_message(441399484, traceback.format_exc())
            dnd.answer_callback_query(call.id, 'Такого эффекта не существует!', show_alert=True)
            return
        users2.update_one({'id': user['id']}, {'$set': {'current_effect': effect['id'], 'current_effectstat': what}})
        text = ''
        if what == 'custom_text':
            text = ' Текущее значение: "'+str(effect['custom_text'])+'".\nВозможные переменные:\n{target_name} - имя цели;\n'+\
            '{effect_name} - название эффекта;\n{unit_name} - имя юнита.'
        elif what == 'condition':
            cond = effect['condition']
            kb = create_condition_kb(cond, effect)
            medit('Выберите условия применения эффекта "'+effect['name']+'"', call.message.chat.id, call.message.message_id, reply_markup = kb)
            return
        users.update_one({'id':user['id']},{'$set':{'current_effect':str(effect['id']), 'current_effectstat':what}})
        dnd.send_message(call.message.chat.id,
                         'Теперь пришлите мне новое значение характеристики эффекта "' + what + '".' + text)
      
        
    elif 'cond_ch' in call.data:
        what = call.data.split(' ')[1]
        try:
            effect = user['effects'][call.data.split(' ')[2]]
        except:
            dnd.answer_callback_query(call.id, 'Такого условия не существует!')
            return
        users.update_one({'id':user['id']},{'$set':{'current_obj':call.data.split(' ')[2]}})
        users.update_one({'id':user['id']},{'$set':{'current_condition':what}})
        text = ''
        if what == 'chance':
            text += ' Выставьте значение типа double, от 0 до 100, обозначающее шанс применения эффекта. Примеры: 0.01; 25; 99; 50.88.'
        dnd.send_message(call.message.chat.id, 'Теперь пришлите мне новое значение пункта "'+what+'".'+text)
        
        
        

    elif 'spell_manage' in call.data:
        try:
            spell = user['spells'][call.data.split(' ')[0]]
        except:
            dnd.answer_callback_query(call.id, 'Такого спелла не существует!', show_alert=True)
            return
        kb = create_spell_kb(spell)
        dnd.send_message(call.message.chat.id, 'Нажмите на характеристику для её изменения.', reply_markup=kb)


    elif 'effect_manage' in call.data:
        try:
            effect = user['effects'][call.data.split(' ')[0]]
        except:
            dnd.answer_callback_query(call.id, 'Такого эффекта не существует!', show_alert=True)
            return
        kb = create_effect_kb(effect)
        dnd.send_message(call.message.chat.id, 'Нажмите на характеристику для её изменения.', reply_markup=kb)
        
    elif 'weapon_manage' in call.data:
        try:
            weapon = user['weapons'][call.data.split(' ')[0]]
        except:
            dnd.send_message(441399484, traceback.format_exc())
            dnd.answer_callback_query(call.id, 'Такого оружия не существует!', show_alert=True)
            return
        kb = create_weapon_kb(weapon)
        dnd.send_message(call.message.chat.id, 'Нажмите на характеристику для её изменения.', reply_markup=kb)
    
    elif 'show' in call.data:
        if call.data.split(' ')[1] == 'id':
            dnd.send_message(call.message.chat.id, 'id объекта: `'+call.data.split(' ')[2]+'`', parse_mode='markdown')
    
    elif 'addt' in call.data:
        team = call.data.split(' ')[1]
        try:
            game = games[int(call.data.split(' ')[2])]
        except:
            dnd.answer_callback_query(call.id, 'Игры не существует!', show_alert = True)
            return
        if call.from_user.id == game['master']['id']:
            users.update_one({'id':user['id']},{'$set':{'current_team':team, 'current_game':game['id']}})
            dnd.send_message(call.message.chat.id, 'Теперь пришлите ID юнита, которого нужно добавить в команду '+team+'.')
        else:
            dnd.answer_callback_query(call.id, 'Только Мастер может добавлять в игру персонажей!', show_alert = True)
      
    elif 'game mainmenu' in call.data:
        try:
            game = games[int(call.data.split(' ')[3])]
        except:
            dnd.answer_callback_query(call.id, 'Игры не существует!')
            return
        try:
            unit = game['units'][int(call.data.split(' ')[2])]
        except:
            try:
                unit = game['units'][call.data.split(' ')[2]]
            except:
                dnd.answer_callback_query(call.id, 'Юнита не существует!', show_alert = True)
                return
            
        kb = mainmenu(game, unit)
        medit('Выберите действие персонажа '+unit['name']+'.', call.message.chat.id, call.message.message_id, reply_markup=kb)
        
        
        
        
    
    elif 'gameact' in call.data:
        try:
            game = games[int(call.data.split(' ')[3])]
        except:
            dnd.answer_callback_query(call.id, 'Игры не существует!')
            return
        nothit = []
        try:
            unit = game['units'][int(call.data.split(' ')[2])]
        except:
            try:
                unit = game['units'][call.data.split(' ')[2]]
            except:
                dnd.answer_callback_query(call.id, 'Юнита не существует!', show_alert = True)
                return
        if game['current_unit'] != str(unit['id']):
            dnd.answer_callback_query(call.id, 'Сейчас не ваш ход!')
            medit('Старое сообщение!', call.message.chat.id, call.message.message_id)
            return
        act = call.data.split(' ')[1]
        tt = ''
        if act == 'select_attack':
            kb = types.InlineKeyboardMarkup()
            for ids in game['units']:
                unit2 = game['units'][ids]
                if unit['team'] != unit2['team']:
                    if unit2['alive'] == True:
                        if unit2['position_code'] == unit['position_code'] or unit['current_weapon']['range'] == 'ranged':
                            kb.add(types.InlineKeyboardButton(text = unit2['name'], callback_data = 'selectact attack '+str(unit['id'])+' '+str(game['id'])+' '+str(unit2['id'])))
                        else:
                            nothit.append(unit2['name'])
            kb.add(types.InlineKeyboardButton(text = 'В главное меню', callback_data = 'game mainmenu '+str(unit['id'])+' '+str(game['id'])))
            if len(nothit) > 0:
                tt += ' Цели, до которых ваше оружие не может достать:\n'
                for ids in nothit:
                    tt += ids+', '
                tt = tt[:len(tt)-2]
                tt += '.'
            medit('Выберите цель.'+tt, call.message.chat.id, call.message.message_id, reply_markup=kb)
        
        elif act == 'select_move':
            melee = []
            kb = types.InlineKeyboardMarkup()
            for ids in game['units']:
                unit2 = game['units'][ids]
                if unit2['alive'] == True:
                    if unit2['position_code'] != unit['position_code']:
                        kb.add(types.InlineKeyboardButton(text = unit2['name'], callback_data = 'selectact move '+str(unit['id'])+' '+str(game['id'])+' '+str(unit2['id'])))
                    else:
                        melee.append(unit2)
            kb.add(types.InlineKeyboardButton(text = 'Отойти ото всех', callback_data = 'selectact move '+str(unit['id'])+' '+str(game['id'])+' '+str(unit['id'])))
            kb.add(types.InlineKeyboardButton(text = 'В главное меню', callback_data = 'game mainmenu '+str(unit['id'])+' '+str(game['id'])))
            if len(melee) > 0:
                tt += ' Бойцы рядом с вами:\n'
                for ids in melee:
                    if ids['id'] != unit['id']:
                        tt += ids['name']+', '
                tt = tt[:len(tt)-2]
                tt += '.'
            medit('Выберите бойца.'+tt, call.message.chat.id, call.message.message_id, reply_markup=kb)
            
        elif act == 'select_speech':
            if unit['speeched'] == False:
                unit['speech_wait'] = True
                users.update_one({'id':call.from_user.id},{'$set':{'cgame':game['id']}})
                medit('Напишите речь юнита следующим сообщением.', call.message.chat.id, call.message.message_id)
            else:
                dnd.send_message(call.message.chat.id, 'Юнит уже говорил на этом ходу!')
                kb = mainmenu(game, unit)
                dnd.send_message(unit['player'], 'Выберите действие.', reply_markup=kb)
                
        elif act == 'select_spell':
            kb = types.InlineKeyboardMarkup()
            text = 'Выберите заклинание. Осталось использований:\n'
            for ids in unit['max_spells']:
                i = unit['max_spells'][ids]
                text += ids+' уровень: '+str(i)+' заклинаний\n'
            for ids in unit['spells']:
                spell = unit['spells'][ids]
                try:
                    sl = unit['max_spells'][str(spell['lvl'])]
                except:
                    try:
                        sl = unit['max_spells'][int(spell['lvl'])]
                    except:
                        sl = 'inf'
                try:
                    if sl > 0:                 
                        kb.add(types.InlineKeyboardButton(text = '('+str(spell['lvl'])+')'+spell['name'], 
                                      callback_data = 'gameact use_spell '+str(unit['id'])+' '+str(game['id'])+' '+str(spell['id']))) 
                except:
                    kb.add(types.InlineKeyboardButton(text = '('+str(spell['lvl'])+')'+spell['name'], 
                                      callback_data = 'gameact use_spell '+str(unit['id'])+' '+str(game['id'])+' '+str(spell['id']))) 
              
            kb.add(types.InlineKeyboardButton(text = 'В главное меню', callback_data = 'game mainmenu '+str(unit['id'])+' '+str(game['id'])))
            medit(text, call.message.chat.id, call.message.message_id, reply_markup = kb)
            
        elif act == 'use_spell':
            try:
                spell = unit['spells'][str(call.data.split(' ')[4])]
            except:
                dnd.answer_callback_query(call.id, 'Спелла не существует!')
                return
            ttypes = ['enemy', 'ally', 'ally!self', 'any', 'any!self']
            if spell['target_type'] in ttypes:
                kb = types.InlineKeyboardMarkup()
                text = 'Выберите цель для заклинания "'+spell['name']+'":'
                
                if spell['target_type'] == 'enemy':
                    for ids in game['units']:
                        enemy = game['units'][ids]
                        if enemy['team'] != unit['team']:
                            kb.add(types.InlineKeyboardButton(text = enemy['name'], 
                                                  callback_data = 'gameact select_spelltarget '+str(unit['id'])+' '+str(game['id'])+' '+str(spell['id'])+' '+str(enemy['id'])))
                elif spell['target_type'] == 'ally':
                    for ids in game['units']:
                        enemy = game['units'][ids]
                        if enemy['team'] == unit['team']:
                            kb.add(types.InlineKeyboardButton(text = enemy['name'], 
                                                  callback_data = 'gameact select_spelltarget '+str(unit['id'])+' '+str(game['id'])+' '+str(spell['id'])+' '+str(enemy['id'])))
                            
                elif spell['target_type'] == 'ally!self':
                    for ids in game['units']:
                        enemy = game['units'][ids]
                        if enemy['team'] == unit['team'] and enemy['id'] != unit['id']:
                            kb.add(types.InlineKeyboardButton(text = enemy['name'], 
                                                  callback_data = 'gameact select_spelltarget '+str(unit['id'])+' '+str(game['id'])+' '+str(spell['id'])+' '+str(enemy['id'])))
                            
                elif spell['target_type'] == 'any':
                    for ids in game['units']:
                        enemy = game['units'][ids]
                        kb.add(types.InlineKeyboardButton(text = enemy['name'], 
                                              callback_data = 'gameact select_spelltarget '+str(unit['id'])+' '+str(game['id'])+' '+str(spell['id'])+' '+str(enemy['id'])))
                       
                elif spell['target_type'] == 'any!self':
                    for ids in game['units']:
                        enemy = game['units'][ids]
                        if enemy['id'] != unit['id']:
                            kb.add(types.InlineKeyboardButton(text = enemy['name'], 
                                                  callback_data = 'gameact select_spelltarget '+str(unit['id'])+' '+str(game['id'])+' '+str(spell['id'])+' '+str(enemy['id'])))
                            
                            
                kb.add(types.InlineKeyboardButton(text = 'В главное меню', callback_data = 'game mainmenu '+str(unit['id'])+' '+str(game['id'])))
                medit('Выберите цель для заклинания "'+spell['name']+'".', call.message.chat.id, call.message.message_id, reply_markup=kb)
                            
            else:
                unit['current_act'] = createact(unit, spell['target_type'], game, 'spell', spell['id'])
                medit('Выбрано: заклинание "'+spell['name']+'".', call.message.chat.id, call.message.message_id)
                game['current_unit'] = None
                unit['done_turn'] = True
                endturn(game, unit)
        
        elif act == 'select_spelltarget':
            try:
                spell = unit['spells'][call.data.split(' ')[4]]
            except:
                dnd.answer_callback_query(call.id, 'Спелла не существует!')
                return
            try:
                target = game['units'][int(call.data.split(' ')[5])]
            except:
                target = game['units'][call.data.split(' ')[5]]
            unit['current_act'] = createact(unit, target, game, 'spell', spell['id'])
            medit('Выбрано: заклинание "'+spell['name']+'", цель - '+target['name'], call.message.chat.id, call.message.message_id)
            game['current_unit'] = None
            unit['done_turn'] = True
            endturn(game, unit)
        
    elif 'selectact' in call.data:
        try:
            game = games[int(call.data.split(' ')[3])]
        except:
            dnd.answer_callback_query(call.id, 'Игры не существует!')
            return
        unit = game['units'][int(call.data.split(' ')[2])]
        if game['current_unit'] != str(unit['id']):
            dnd.answer_callback_query(call.id, 'Сейчас не ваш ход!')
            medit('Старое сообщение!', call.message.chat.id, call.message.message_id)
            return
        act = call.data.split(' ')[1]
        if act == 'attack':
            target = game['units'][int(call.data.split(' ')[4])]
            unit['current_act'] = createact(unit, target, game, 'attack')
            medit('Выбрано: атака '+target['name']+'.', call.message.chat.id, call.message.message_id)
            unit['done_turn'] = True
            endturn(game, unit)
        elif act == 'move':
            target = game['units'][int(call.data.split(' ')[4])]
            unit['current_act'] = createact(unit, target, game, 'move')
            if unit['id'] != target['id']:
                medit('Выбрано: передвижение к '+target['name']+'.', call.message.chat.id, call.message.message_id)
            else:
                medit('Выбрано: отход.', call.message.chat.id, call.message.message_id)
            game['current_unit'] = None
            unit['done_turn'] = True
            endturn(game, unit)
  except:
    dnd.send_message(441399484, traceback.format_exc()) 
            
def endturn(game, unit):
    if unit['done_turn'] == False:
        medit('Время вышло!', game['current_msg'].chat.id, game['current_msg'].message_id)
    game['current_unit'] = None
    if game['ctimer'] != None:
        try:
            game['ctimer'].cancel()
        except:
            dnd.send_message(441399484, traceback.format_exc())
    if unit['current_act'] == None:
        dnd.send_message(game['id'], unit['name']+' решил почиллить вместо действий! Передаю ход.')
        game['now_unit'] += 1
        next_turn(game)
        return
    if unit['current_act']['act'] == 'attack':
        hit(unit, game)
        dnd.send_message(game['id'], 'Следующий ход!')
        game['now_unit'] += 1
        time.sleep(1)
        next_turn(game)
                
    elif unit['current_act']['act'] == 'move':
        target = unit['current_act']['target']
        text = ''
        
        freeatk = []    
        for ids in game['units']:
            unit2 = game['units'][ids]
            if unit2['team'] != unit['team'] and unit2['position_code'] == unit['position_code'] and unit2['freeatk'] > 0 and unit2['alive']:
                freeatk.append(unit2)
            
        if target['id'] == unit['id']:
            unit['position_code'] = poscodegen(game = game)
            text += '👣|'+unit['name']+' отходит подальше ото всех!\n'
        else:
            unit['position_code'] = target['position_code']
            text += '👣|'+unit['name']+' подходит к '+target['name']+' вплотную!\n'
        dnd.send_message(game['id'], text)
        time.sleep(2)
        fatext = ''
        if len(freeatk) > 0:
            fatext += 'Свободные атаки по '+unit['name']+' за выход из ближнего боя:'
            dnd.send_message(game['id'], fatext)
            time.sleep(1)
            for ids in freeatk:
                hit(ids, game, target = unit)
                ids['freeatk'] -= 1
            time.sleep(1)
            
        dnd.send_message(game['id'], 'Следующий ход!')
        time.sleep(1)
        game['now_unit'] += 1
        next_turn(game)
    
    elif unit['current_act']['act'] == 'spell':
        try:
            spell = unit['spells'][int(unit['current_act']['spell'])]
        except:
            spell = unit['spells'][str(unit['current_act']['spell'])]
        try:
            unit['max_spells'][spell['lvl']] -= 1
        except:
            pass
        target = unit['current_act']['target']
        notarget = ['all_ally', 'all_enemy', 'self', 'all_ally!self', 'all!self', 'all']
        targets = []
        dt = ''
        add_d = False
        if target in notarget:
            if target == 'all_ally':
                for ids in game['units']:
                    enemy = game['units'][ids]
                    if enemy['team'] == unit['team'] and enemy['alive']:
                        targets.append(enemy)
                        
            elif target == 'all_enemy':
                for ids in game['units']:
                    enemy = game['units'][ids]
                    if enemy['team'] != unit['team'] and enemy['alive']:
                        targets.append(enemy)
                        
            elif target == 'self':
                targets.append(unit)
                
            elif target == 'all_ally!self':
                for ids in game['units']:
                    enemy = game['units'][ids]
                    if enemy['team'] == unit['team'] and enemy['id'] != unit['id'] and enemy['alive']:
                        targets.append(enemy)

            elif target == 'all!self':
                for ids in game['units']:
                    enemy = game['units'][ids]
                    if enemy['id'] != unit['id'] and enemy['alive']:
                        targets.append(enemy)
                        
            elif target == 'all':
                for ids in game['units']:
                    enemy = game['units'][ids]
                    if enemy['alive']:
                        targets.append(enemy)
            
                        

        
        else:
            targets.append(game['units'][target['id']])
            if spell['damage_type'] == 'aoe':
                for ids in game['units']:
                    if game['units'][ids]['position_code'] == target['position_code'] and game['units'][ids]['id'] != target['id'] and target['alive']:
                        targets.append(game['units'][ids])
                        add_d = True
        letter = 'е'
        if add_d:
            dt += ' и все стоящие рядом существа'
            letter = 'ю'
                
                    
        text = ''
        text += unit['name']+' использует заклинание "'+spell['name']+'"!'
        if spell['custom_text'] != None:
            text = ''
            text = spell['custom_text']
            text = text.replace('{unit_name}', unit['name']).replace('{spell_name}', spell['name'])
            if target not in notarget:
                text = text.replace('{target_name}', target['name'])
        heal = 0
        damage = 0
        if target == 'all_ally':
            text += ' Все союзники получают следующее:\n'
        elif target == 'all_enemy':
            text += ' Все враги получают следующее:\n'
        elif target == 'self':
            text += ' Он получает следующее:\n'
        elif target == 'all_enemy!self':
            text += ' Все союзники, кроме него самого, получают следующее:\n'
        elif target == 'all!self':
            text += ' Все персонажи, кроме него, получают следующее:\n'
        elif target == 'all':
            text += ' Все персонажи получают следующее:\n'       
        else:
            text += ' '+target['name']+dt+' получа'+letter+'т следующее:\n'
            
        try:
            spell['heal'] += 0
            tp = 'static'
        except:
            tp = 'random'
            
        if tp == 'static':
            if spell['heal'] > 0:
                heal += spell['heal']
                text += '♥|Отхил на '+str(spell['heal'])+' хп!\n'
                
        else:
            heal = 0
            i = 0
            need = int(spell['heal'].split('d')[0])
            while i < need:
                heal += random.randint(1, int(spell['heal'].split('d')[1]))
                i+=1
            text += '♥|Отхил на ('+spell['heal']+') = '+str(heal)+' хп!\n'
        
        try:
            spell['damage'] += 0
            tp = 'static'
        except:
            tp = 'random'
            
        if tp == 'static':
            if spell['damage'] > 0:
                damage += spell['damage']
                text += '💔|Урон: '+str(spell['damage'])+' единиц(ы)!\n'
                
        else:
            damage = 0
            i = 0
            need = int(spell['damage'].split('d')[0])
            while i < need:
                damage += random.randint(1, int(spell['damage'].split('d')[1]))
                i+=1
            text += '💔|Урон: ('+spell['damage']+') = '+str(damage)+' единиц!\n'
          
        dnd.send_message(game['id'], text)
        time.sleep(2)
        text = ''
        for ids in targets:
            dt = ''
            if heal > 0:
                ids['hp'] += heal
                if ids['hp'] > ids['maxhp']:
                    ids['hp'] = ids['maxhp']
            if damage > 0:
                attr = spell['savethrow']['attribute']
                border = spell['savethrow']['value']
                bonus = int((unit[attr]-10)/2)
                result = random.randint(1,20)
                if result + bonus >= border:
                    r = 'успех! Получает только половину ('+str(int(damage/2))+') урона.'
                    ids['hp'] -= int(damage/2)
                    if deathtest(ids):
                        ids['alive'] = False
                        dt += '\n☠|'+ids['name']+' погибает!'
                    em = '👍'
                else:
                    r = 'неудача!'
                    em = '👎'
                    ids['hp'] -= damage
                    if deathtest(ids):
                        ids['alive'] = False
                        dt += '\n☠|'+ids['name']+' погибает!'
                    
                text += ids['name']+' делает спасбросок аттрибута "'+attr+'" по сложности '+ \
                str(border)+': (1d20 + '+str(bonus)+') = '+str(result + bonus)+'.\n'+em+'|'+r+dt+'\n\n'
        if text != '':
            dnd.send_message(game['id'], text)
        time.sleep(2)
        dnd.send_message(game['id'], 'Следующий ход!')
        game['now_unit'] += 1
        time.sleep(1)
        next_turn(game)
                        
                    
                    
                
def deathtest(unit):
    if unit['hp'] <= 0:
        return True
    else:
        return False
                
                
        
def hit(unit, game, target = None):
    if target == None:
        target = unit['current_act']['target']
    text = ''
    em = '💥'
    bonus = unit['current_weapon']['accuracy_buff'] #int((unit['dexterity']-10)/2)
    text += em+'|'+unit['name']+' атакует '+target['name']+', используя '+unit['current_weapon']['name']+'!'
    t2 = ' Кидает на попадание (1d20 + '+str(bonus)+')'
    try:
        if unit['current_weapon']['custom_attack_text'] != None:
            text = unit['current_weapon']['custom_attack_text']
            text = text.replace('{unit_name}', unit['name']).replace('{target_name}', target['name']).replace('{weapon_name}', unit['current_weapon']['name'])
    except:
        pass
    text += t2
        
    dnd.send_message(game['id'], text)
    time.sleep(2)
    text = ''
    bonus = unit['current_weapon']['accuracy_buff']
    hit = random.randint(1, 20) + bonus
    text += str(hit)+'! Армор-класс соперника: '+str(target['armor_class'])+'🛡. '
    if target['armor_class'] >= hit:
        text += '💨Промах!'
        h = False
    else:
        text += '💥Попадание!'
        h = True
    dnd.send_message(game['id'], text)
    time.sleep(2)
    if h:
        bonusdmg = 0
        bonusstun = 0
        eftext = ''
        w = unit['current_weapon']
        for ids in w['effects']:
            effect = w['effects'][ids]
            damount = str(effect['condition']['chance'])
            try:
                d = damount.split('.')[1]
            except:
                try:
                    d = damount.split(',')[1]
                except:
                    d = ''
            x = int('100'+('0'*len(d)))
            chance = (x*float(effect['condition']['chance']))/100
            print(chance)
            print(x)
            print(effect['condition']['chance'])
            allow = True
            sign = None
            for idss in effect['condition']['target_stats']:
                try:
                    x = effect['condition']['target_stats']
                    value = int(x[idss])
                except:
                    value = x[idss]
                    if value[0] in ['>', '<', '=']:
                        sign = value[0]
                        try:
                            value = int(value[1:])
                        except:
                            value = 0
                if sign != None:
                    if sign == '>':
                        try:
                            if target[idss] <= value:
                                allow = False
                        except:
                            pass
                    elif sign == '<':
                        try:
                            if target[idss] >= value:
                                allow = False
                        except:
                            pass
                    elif sign == '=':
                        try:
                            if target[idss] != value:
                                allow = False
                        except:
                            pass
                else:
                    if target[idss] != value:
                        allow = False
                        
            for idss in effect['condition']['unit_stats']:
                try:
                    x = effect['condition']['target_stats']
                    value = int(x[idss])
                except:
                    value = x[idss]
                    if value[0] in ['>', '<', '=']:
                        sign = value[0]
                        try:
                            value = int(value[1:])
                        except:
                            value = 0
                if sign != None:
                    if sign == '>':
                        try:
                            if unit[idss] <= value:
                                allow = False
                        except:
                            pass
                    elif sign == '<':
                        try:
                            if unit[idss] >= value:
                                allow = False
                        except:
                            pass
                    elif sign == '=':
                        try:
                            if unit[idss] != value:
                                allow = False
                        except:
                            pass
                else:
                    if unit[idss] != value:
                        allow = False
            if random.randint(1, x) <= chance and allow:
                try:
                    if effect['effect'] == 'crit':
                        try:
                            int(effect['power'])
                            tp = 'static'
                        except:
                            tp = 'random'
                        if tp == 'static':
                            if effect['target'] == 'target':
                                bonusdmg += int(effect['power'])
                                eftext += '💔|Крит: цель дополнительно получает '+str(bonusdmg)+' урона!\n'
                            else:
                                unit['hp'] -= int(effect['power'])
                                eftext += '💔|'+unit['name']+' теряет '+str(effect['power'])+' хп!\n'
                                
                        else:
                            damage = 0
                            i = 0
                            need = int(effect['power'].split('d')[0])
                            while i < need:
                                bonusdmg += random.randint(1, int(effect['power'].split('d')[1]))
                                i+=1
                            if effect['target'] == 'target':
                                eftext += '💔|Крит: цель дополнительно получает ('+effect['power']+') = '+str(bonusdmg)+' урона!\n'
                            else:
                                unit['hp'] -= bonusdmg
                                eftext += '💔|'+unit['name']+' теряет '+str(bonusdmg)+' хп!\n'
                                bonusdmg = 0
                                
                    elif effect == 'stun':
                        try:
                            int(effect['power'])
                            tp = 'static'
                        except:
                            tp = 'random'
                        if tp == 'static':
                            if effect['target'] == 'target':
                                bonusstun += int(effect['power'])+1
                                eftext += '🌀|Оглушение: цель пропустит следующие '+str(bonusstun-1)+' ходов!\n'
                            else:
                                unit['stunned'] += int(effect['power'])+1
                                eftext += '🌀|Оглушение: '+unit['name']+' пропустит следующие '+str(effect['power'])+' ходов!\n'
                                
                        else:
                            bonusstun = 0
                            i = 0
                            need = int(effect['power'].split('d')[0])
                            while i < need:
                                bonusstun += random.randint(1, int(effect['power'].split('d')[1]))
                                i+=1
                            bonusstun += 1
                            if effect['target'] == 'target':
                                eftext += '🌀|Оглушение: цель пропустит следующие ('+effect['power']+') = '+str(bonusstun-1)+' ходов!\n'
                            else:
                                unit['stunned'] += bonusstun
                                eftext += '🌀|'+unit['name']+' пропустит следующие '+str(bonusstun-1)+' ходов!\n'
                                bonusstun = 0
                        
                        
                        
                except:
                    dnd.send_message(441399484, traceback.format_exc())
                    eftext = 'Криво выставлена переменная "power" эффекта '+effect['name']+' персонажа '+unit['name']+'! Отменяю эффект.'
                            
        if eftext != '':
            dnd.send_message(game['id'], 'Эффекты:\n'+eftext)  
            time.sleep(2)
        weapon = unit['current_weapon']
        totaldmg = random.randint(1, weapon['maxdmg']) + weapon['dmg_buff'] + bonusdmg
        buff = 0
        buff += weapon['dmg_buff'] + bonusdmg
        text = '💔|Нанесённый урон: ('+str(1)+'d'+str(weapon['maxdmg'])+' + '+str(buff)+') = '+str(totaldmg)+'!' 
        dnd.send_message(game['id'], text)
        time.sleep(2)
        text = ''
        target['stunned'] += bonusstun
        target['hp'] -= totaldmg
        dd = False
        if target['hp'] <= 0:
            target['alive'] = False
            dd = True
        if dd:
            text += '☠|'+target['name']+' погибает!'
        else:
            text += 'У '+target['name']+' остаётся '+str(target['hp'])+'♥!'
        dnd.send_message(game['id'], text)
        time.sleep(2)
    else:
        pass


effects = ['stun', 'weakness', 'kill', 'mark', 'bonus_accuracy', 'bonus_strenght', 'bonus_dexterity', 'bonus_wisdom', 'crit'
              'bonus_charisma', 'bonus_constitution', 'bonus_intelligence', 'bonus_armor', 'bonus_maxhp', 'bonus_hp', 'respawn']
    
        
def createact(unit, target, game, act, spell = None):
    if act == 'attack' or act == 'move':
        return {
            'act':act,
            'target':target
        }
    elif act == 'spell':
        return {
            'act':act,
            'target':target,
            'spell':spell
        }
  


def next_turn(game):
    if game['kill']:
        del games[game['id']]
        return
    reset_vars(game)
    if len(game['units']) <= 1:
        dnd.send_message(game['id'], 'Ничья! Все мертвы!')
        del games[game['id']]
        return
    teams = {}
    for ids in game['units']:
        unit = game['units'][ids]
        if unit['alive']:
            if unit['team'] not in teams:
                teams.update({unit['team']:1})
            else:
                teams[unit['team']]+=1
    end = False
    aliveteams = 0
    if len(teams) <= 1:
        end = True
    if end:
        if len(teams) == 0:
            text = 'Все проиграли!'
        else:
            for ids in teams:
                team = ids
            text = 'Команда '+team+' победила! Выжившие бойцы:\n'
            for ids in game['units']:
                unit = game['units'][ids]
                if unit['alive']:
                    text += unit['name']+': '+str(unit['hp'])+'/'+str(unit['maxhp'])+'♥️!\n'
        dnd.send_message(game['id'], 'Игра окончена! Результаты:\n'+text)
        del games[game['id']]
        return
        
    cunit = None
    while cunit == None:
        for ids in game['units']:
            unit = game['units'][ids]
            if unit['turn'] == game['now_unit'] and unit['alive']:
                cunit = unit
        if cunit == None:
            if game['now_unit'] > len(game['units']):
                game['now_unit'] = 1
            else:
                game['now_unit'] += 1
    game['current_unit'] = str(cunit['id'])
    dnd.send_message(game['id'], 'Ход юнита '+cunit['name']+'!')
    give_turn(game, cunit)
    
    
def reset_vars(game):
    for ids in game['units']:
        unit = game['units'][ids]
        unit['current_act'] = None
        unit['speech_wait'] = False
        unit['speeched'] = False
        unit['done_turn'] = False
        unit['stunned'] -= 1
        if unit['stunned'] < 0:
            unit['stunned'] = 0
    
    
def give_turn(game, unit):
    unit['freeatk'] = 1
    user = users.find_one({'id':unit['player']})
    if user == None:
        dnd.send_message(game['id'], 'Не знаю юзера, управляющего персонажем '+unit['name']+'! Передаю ход.')
        time.sleep(1)
        game['now_unit'] += 1
        next_turn(game)
        return
    if unit['stunned'] > 0:
        dnd.send_message(game['id'], '🌀|'+unit['name']+' оглушен! Передаю ход.')
        time.sleep(1)
        game['now_unit'] += 1
        next_turn(game)
        return
    kb = mainmenu(game, unit)
    try:
        timee = 70
        msg = dnd.send_message(unit['player'], 'Выберите действие персонажа '+unit['name']+'! У вас '+str(timee)+' секунд.', reply_markup=kb)
        game['current_msg'] = msg
        t = threading.Timer(timee, endturn, args = [game, unit])
        t.start()
        game['ctimer'] = t
    except:
        dnd.send_message(441399484, traceback.format_exc())
        dnd.send_message(game['id'], 'Управляющий персонажем '+unit['name']+' не написал мне в личку! Передаю ход.')
        time.sleep(1)
        game['now_unit'] += 1
        next_turn(game)
        return
   
                                                               
def say_speech(unit, game, text):
    if unit['photo'] == None:
        dnd.send_message(game['id'], unit['name']+': '+text)
    else:
        dnd.send_photo(game['id'], unit['photo'], caption = unit['name']+': '+text)
    unit['speech_wait'] = False
    unit['speeched'] = True
    kb = mainmenu(game, unit)
    dnd.send_message(unit['player'], 'Выберите действие.', reply_markup=kb)
                                                               
                                                               
                                                               


def mainmenu(game, unit):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text = 'Атака', callback_data = 'gameact select_attack '+str(unit['id'])+' '+str(game['id'])), 
           types.InlineKeyboardButton(text = 'Заклинание', callback_data = 'gameact select_spell '+str(unit['id'])+' '+str(game['id']))
          )
    kb.add(types.InlineKeyboardButton(text = 'Реакция', callback_data = 'gameact select_reaction '+str(unit['id'])+' '+str(game['id'])), 
           types.InlineKeyboardButton(text = 'Движение', callback_data = 'gameact select_move '+str(unit['id'])+' '+str(game['id']))
          )
    kb.add(types.InlineKeyboardButton(text = 'Свободная речь', callback_data = 'gameact select_speech '+str(unit['id'])+' '+str(game['id'])))
    return kb

def sendunitedit(id, unit):
    kb = create_edit_kb(unit)
    dnd.send_message(id, 'Нажмите на характеристику для её изменения.', reply_markup=kb)


def sendspelledit(id, spell):
    kb = create_spell_kb(spell)
    dnd.send_message(id, 'Нажмите на характеристику для её изменения.', reply_markup=kb)
    
def sendweaponedit(id, weapon):
    kb = create_weapon_kb(weapon)
    dnd.send_message(id, 'Нажмите на характеристику для её изменения.', reply_markup=kb)


def create_spell_kb(spell):
    kb = types.InlineKeyboardMarkup()
    kb.add(addkb(kb, 'Название: ' + spell['name'], 'spell_change name ' + str(spell['id'])))
    kb.add(addkb(kb, 'ID: ' + str(spell['id']), 'show id ' + str(spell['id'])))
    kb.add(addkb(kb, 'Классы: ' + str(spell['classes']), 'spell_change classes ' + str(spell['id'])))
    kb.add(addkb(kb, 'Описание: ' + str(spell['description']), 'spell_change description ' + str(spell['id'])))
    kb.add(addkb(kb, 'Уровень: ' + str(spell['lvl']), 'spell_change lvl ' + str(spell['id'])))
    kb.add(addkb(kb, 'Тип целей: ' + str(spell['target_type']), 'spell_change target_type ' + str(spell['id'])))
    kb.add(addkb(kb, 'Урон: ' + str(spell['damage']), 'spell_change damage ' + str(spell['id'])))
    kb.add(addkb(kb, 'Лечение: ' + str(spell['heal']), 'spell_change heal ' + str(spell['id'])))
    kb.add(addkb(kb, 'Спасбросок: ' + str(len(spell['savethrow']))+' свойства', 'spell_change savethrow ' + str(spell['id'])))
    kb.add(addkb(kb, 'Тип урона: ' + str(spell['damage_type']), 'spell_change damage_type ' + str(spell['id'])))
    kb.add(addkb(kb, 'Эффекты: ' + str(len(spell['effects']))+' эффектов', 'spell_change effects ' + str(spell['id'])))
    kb.add(addkb(kb, 'Кастомный текст применения: ' + str(spell['custom_text']), 'spell_change custom_text ' + str(spell['id'])))
    return kb


def create_weapon_kb(weapon):
    kb = types.InlineKeyboardMarkup()
    kb.add(addkb(kb, 'Название: ' + weapon['name'], 'weapon_ch name ' + str(weapon['id'])))
    kb.add(addkb(kb, 'ID: ' + str(weapon['id']), 'show id ' + str(weapon['id'])))
    kb.add(addkb(kb, 'Максимальный урон: ' + str(weapon['maxdmg']), 'weapon_ch maxdmg ' + str(weapon['id'])))
    kb.add(addkb(kb, 'Бонус урона: ' + str(weapon['dmg_buff']), 'weapon_ch dmg_buff ' + str(weapon['id'])))
    kb.add(addkb(kb, 'Бонус точности: ' + str(weapon['accuracy_buff']), 'weapon_ch accuracy_buff ' + str(weapon['id'])))
    kb.add(addkb(kb, 'Тип: ' + str(weapon['range']), 'weapon_ch range ' + str(weapon['id'])))
    kb.add(addkb(kb, 'Эффекты: ' + str(len(weapon['effects']))+' эффектов', 'weapon_ch effects ' + str(weapon['id'])))
    kb.add(addkb(kb, 'Кастомный текст атаки', 'weapon_ch custom_attack_text ' + str(weapon['id'])))
    return kb

def create_effect_kb(effect):
    kb = types.InlineKeyboardMarkup()
    kb.add(addkb(kb, 'Название: ' + effect['name'], 'effect_ch name ' + str(effect['id'])))
    kb.add(addkb(kb, 'ID: ' + str(effect['id']), 'show id ' + str(effect['id'])))
    kb.add(addkb(kb, 'Условие', 'effect_ch condition ' + str(effect['id'])))
    kb.add(addkb(kb, 'Эффект: '+effect['effect'], 'effect_ch effect ' + str(effect['id'])))
    kb.add(addkb(kb, 'Мощность: '+str(effect['power']), 'effect_ch power ' + str(effect['id'])))
    kb.add(addkb(kb, 'Кто получает эффект: '+str(effect['target']), 'effect_ch target ' + str(effect['id'])))
    kb.add(addkb(kb, 'Длительность (в ходах): '+str(effect['duration']), 'effect_ch duration ' + str(effect['id'])))
    kb.add(addkb(kb, 'Текст наложения: '+str(effect['custom_text']), 'effect_ch custom_text ' + str(effect['id'])))
    return kb


def create_condition_kb(cond, obj):
    kb = types.InlineKeyboardMarkup()
    kb.add(addkb(kb, 'Требуемые статы цели', 'cond_ch target_stats '+str(obj['id'])))
    kb.add(addkb(kb, 'Требуемые статы юнита', 'cond_ch unit_stats '+str(obj['id'])))
    kb.add(addkb(kb, 'Шанс применения: '+str(cond['chance'])+'%', 'cond_ch chance '+str(obj['id'])))
    return kb
            

def create_edit_kb(unit):
    pl = 'Unknown ID'
    user = users.find_one({'id':unit['player']})
    if user != None:
        pl = user['name']
    wname = None
    if unit['current_weapon'] != None:
        wname = unit['current_weapon']['name']
    kb = types.InlineKeyboardMarkup()
    kb.add(addkb(kb, 'Имя: ' + unit['name'], 'change name ' + str(unit['id'])), addkb(kb, 'ID: ' + str(unit['id']), 'show id ' + str(unit['id'])))
    kb.add(addkb(kb, 'Класс: ' + unit['class'], 'change class ' + str(unit['id'])), addkb(kb, 'Раса: ' + unit['race'], 'change race ' + str(unit['id'])))
    kb.add(addkb(kb, 'Хп: ' + str(unit['hp']), 'change hp ' + str(unit['id'])), addkb(kb, 'Макс.хп: ' + str(unit['maxhp']), 'change maxhp ' + str(unit['id'])))
    kb.add(addkb(kb, 'Сила: ' + str(unit['strenght']), 'change strenght ' + str(unit['id'])), addkb(kb, 'Ловкость: ' + str(unit['dexterity']), 'change dexterity ' + str(unit['id'])))
    kb.add(addkb(kb, 'Телосложение: ' + str(unit['constitution']), 'change constitution ' + str(unit['id'])), addkb(kb, 'Интеллект: ' + str(unit['intelligence']), 'change intelligence ' + str(unit['id'])))
    kb.add(addkb(kb, 'Мудрость: ' + str(unit['wisdom']), 'change wisdom ' + str(unit['id'])), addkb(kb, 'Харизма: ' + str(unit['charisma']), 'change charisma ' + str(unit['id'])))
    kb.add(addkb(kb, 'Класс брони: ' + str(unit['armor_class']), 'change armor_class ' + str(unit['id'])))
    kb.add(addkb(kb, 'Инвентарь: ' + str(len(unit['inventory'])) + ' предметов', 'change inventory ' + str(unit['id'])), addkb(kb, 'Заклинания', 'change spells ' + str(unit['id'])))
    kb.add(addkb(kb, 'Максимум спеллов за раунд', 'change max_spells ' + str(unit['id'])))
    kb.add(addkb(kb, 'Оружие: ' + str(wname), 'change current_weapon ' + str(unit['id'])))
    kb.add(addkb(kb, 'Игрок: ' + pl, 'change player ' + str(unit['id'])), addkb(kb, 'Фото', 'change photo ' + str(unit['id'])))
    return kb


def createspell():
    targets = ['all_enemy', 'all_ally', 'enemy', 'ally', 'self', 'all', 'ally!self', 'all_ally!self',
                                     'all!self', 'any', 'any!self']
    id = randomid()
    return {
        'id': id,
        'name': str(id),
        'classes': 'socerer',
        'description': 'Описание спелла',
        'lvl': 0,
        'target_type':random.choice(targets),
        'damage':random.randint(0, 10),
        'heal': random.randint(0, 10),
        'custom_text':None,
        'effects':{},
        'savethrow':{'attribute':'strenght',
                    'value':10},
        'debuffs':{},
        'damage_type':random.choice(['target', 'aoe']),
        'effects':{}
    }


def createweapon():
    id = randomid()
    name = random.choice(['Топорик', 'Кинжал', 'Палка', 'Кулак Смерти', 'Нунчаки', 'Посох'])
    return {
    'id':id,
    'name':name,
    'maxdmg':random.randint(4, 10),
    'dmg_buff':random.randint(0, 3),
    'accuracy_buff':random.randint(0,3),
    'range':random.choice(['melee', 'ranged']),
    'custom_attack_text':None,
    'effects':{}
}



def addkb(kb, text, calldata):
    return types.InlineKeyboardButton(text=text, callback_data=calldata)


def createunit(user = None, userid = None):
    maxx = 20
    minn = 6
    maxhp = random.randint(8, 20)
    if user != None:
        id = user['id']
    else:
        id = userid
    return {
        'id': randomid(),
        'name': randomname(),
        'class': randomclass(),
        'race': randomrace(),
        'hp': maxhp,
        'maxhp': maxhp,
        'strenght': random.randint(minn, maxx),
        'dexterity': random.randint(minn, maxx),
        'constitution': random.randint(minn, maxx),
        'intelligence': random.randint(minn, maxx),
        'wisdom': random.randint(minn, maxx),
        'charisma': random.randint(minn, maxx),
        'armor_class': random.randint(8, 16),
        'initiative': 10,
        'speed': 30,
        'photo': None,
        'death_saves(success)': 0,
        'death_saves(fail)': 0,
        'spells': {},
        'inventory': [],
        'current_weapon': None,
        'owner': id,
        'player': None,
        'max_spells':{}
    }


def createeffect():
    id = randomid()
    name = str(id)
    effects = ['stun', 'weakness', 'kill', 'mark', 'bonus_accuracy', 'bonus_strenght', 'bonus_dexterity', 'bonus_wisdom', 'crit'
              'bonus_charisma', 'bonus_constitution', 'bonus_intelligence', 'bonus_armor', 'bonus_maxhp', 'bonus_hp', 'respawn']
    return {
        'id':id,
        'name':name,
        'condition':createcondition(),
        'effect':random.choice(effects),
        'power':str(random.randint(0, 5)),
        'target':random.choice(['target', 'unit']),
        'duration':random.randint(0, 3),
        'custom_text':None
}


def createcondition():
    return {
        'target_stats':{},
        'unit_stats':{},
        'chance':'100'
    }


def kb_sort(kbs):
    kb = types.InlineKeyboardMarkup()
    i = 0
    nextt = False
    toadd = []
    while i < len(kbs):
        if nextt == True:
            kb.add(*toadd)
            toadd = []
            toadd.append(kbs[i])
            nextt = False
        else:
            toadd.append(kbs[i])
        if i % 2 == 1:
            nextt = True
        i += 1
    kb.add(*toadd)
    return kb

def randomname():
    names = ['Лурин Нвуд', 'Лонг Лао', 'Корза Ксогоголь', 'Алстон Опплбай', 'Холг', 'Лаэл Бит', 'Иглай Тай',
             'Унео Ано', 'Джор Нарарис', 'Кара Чернин', 'Хама Ана', 'Мейлиль Думеин', 'Шаумар Илтазяра',
             'Ромеро Писакар',
             'Шандри Грэйкасл', 'Зэй Тилататна', 'Силусс Ори', 'Чиаркот Литоари', 'Дикай Талаф', 'Чка Хладоклят',
             'Вренн', 'Пупа', 'Лупа', 'Харламов']
    return random.choice(names)


def randomclass():
    return random.choice(classes)


def randomrace():
    return random.choice(races)


def randomid():
    id = nowid.find_one({})['id']
    nowid.update_one({}, {'$inc': {'id': 1}})
    return id + 1


def createuser2(m):
    user = users2.find_one({'id': m.from_user.id})
    if user == None:
        users2.insert_one(createu(m))
        user = users2.find_one({'id': m.from_user.id})
    return user


def createu(m):
    d = {'id': m.from_user.id,
         'name': m.from_user.first_name}

    for ids in base:
        d.update({ids: base[ids]})

    return d


def dmedit(message_text, chat_id, message_id, reply_markup=None, parse_mode=None):
    return dnd.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_text, reply_markup=reply_markup,
                                 parse_mode=parse_mode)


def creategame(m):
    return {m.chat.id:{
        'id':m.chat.id,
        'master':createplayer(m.from_user),
        'turn':1,
        'units':{},
        'started':False,
        'now_unit':1,
        'ctimer':None,
        'kill':False,
        'current_unit':None,
        'current_msg':None
    }
           }
        

def createplayer(user):
            return {
                'id':user.id,
                'name':user.first_name
            }
       
def input_create_unit(userid, slovar):
    values = []
    text = ''
    unit = createunit(userid = userid)
    for ids in slovar:
        try:
            allow = False
            if ids in numbervalues:
                elem = int(slovar[ids])
                allow = True
            elif ids in dicts:
                if type(elem) == dict:
                    allow = True
            elif ids in lists:
                if type(elem) == list:
                    allow = True
            if ids == 'id' or ids == 'owner':
                allow = False
            if allow:
                unit[ids] = elem
            else:
                text += 'Неверный формат элемента '+str(elem)+'!\n'
        except:
            dnd.send_message(441399484, traceback.format_exc())
            text += 'Ошибка при добавлении элемента "'+ids+'"!\n'
    return [unit, text]
        
        
def medit(message_text, chat_id, message_id, reply_markup=None, parse_mode=None):
    return dnd.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_text,
                                    reply_markup=reply_markup,
                                    parse_mode=parse_mode)   
        
def upd_all(prm, value):    
    for ids in users.find({}):
        for idss in ids['spells']:
            print(idss)
            users.update_one({'id':ids['id']},{'$set':{'spells.'+str(idss)+'.'+prm:value}})
        for idss in ids['weapons']:
            users.update_one({'id':ids['id']},{'$set':{'weapons.'+str(idss)+'.'+prm:value}})
        for idss in ids['units']:
            for idsss in ids['units'][idss]['spells']:
                users.update_one({'id':ids['id']},{'$set':{'units.'+idss+'.spells.'+idsss+'.'+prm:value}})
            if ids['units'][idss]['current_weapon'] != None:
                users.update_one({'id':ids['id']},{'$set':{'units.'+idss+'.current_weapon.'+prm:value}})
    x = open_objects.find_one({})
    for idss in x['spells']:
        open_objects.update_one({},{'$set':{'spells.'+str(idss)+'.'+prm:value}})
    for idss in x['weapons']:
        open_objects.update_one({},{'$set':{'weapons.'+str(idss)+'.'+prm:value}})
    for idss in x['units']:
        for idsss in x['units'][idss]['spells']:
            open_objects.update_one({},{'$set':{'units.'+idss+'.spells.'+idsss+'.'+prm:value}})
        if x['units'][idss]['current_weapon'] != None:
            open_objects.update_one({},{'$set':{'units.'+idss+'.current_weapon.'+prm:value}})
                
#upd_all('effects', {})

        
for ids in users2.find({}):
    for idss in base:
        if idss not in ids:
            users2.update_one({'id': ids['id']}, {'$set': {idss: base[idss]}})
            
            
dnd.polling(none_stop = True)




