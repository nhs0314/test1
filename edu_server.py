import socket
import threading
import sqlite3
import sys

PORT = 2090
BUF_SIZE = 1024
lock = threading.Lock()
clnt_imfor = []  # [sock, id, type, state]
clnt_cnt = 0
room_num = 2


# DB 연결, 커서획득 함수
def get_DBcursor():
    con = sqlite3.connect('edu.db')  # DB open
    c = con.cursor()  # 커서 획득
    return (con, c)


# 버퍼 비우고 recv 및 decode
def recv_clnt_msg(clnt_sock):
    sys.stdout.flush()  # 버퍼 비우기
    clnt_msg = clnt_sock.recv(BUF_SIZE)  # 메세지 받아오기
    clnt_msg = clnt_msg.decode()  # 디코딩
    return clnt_msg


# 버퍼 비우고 encode 후 send
def send_clnt_msg(clnt_sock, msg):
    sys.stdin.flush()  # 버퍼 비우기
    msg = msg.encode()  # 인코딩
    clnt_sock.send(msg)  # 메세지 보내기


# 클라이언트 종료시 해당 클라이언트 정보를 clnt_imfor 리스트에서 그 뒤의 정보로 덮어씌움
def delete_imfor(clnt_sock):
    global clnt_cnt
    if clnt_cnt == 1:
        clnt_imfor.clear()
        print('exit client')
    else:
        for i in range(0, clnt_cnt):
            if clnt_sock == clnt_imfor[i][0]:  # 해당 소켓 가진 클라이언트 정보 찾기
                print('exit client')
                while i < clnt_cnt - 1:  # 그 뒤에 있는 클라이언트 정보들을 한 칸씩 앞으로 당겨옴
                    clnt_imfor[i] = clnt_imfor[i + 1]
                    i += 1
                break
    clnt_cnt -= 1


# 회원가입
def sign_up(clnt_num):
    con, c = get_DBcursor()
    clnt_sock = clnt_imfor[clnt_num][0]
    type = clnt_imfor[clnt_num][2]

    while True:
        check = 0
        check_id = recv_clnt_msg(clnt_sock)
        if check_id == "exit":  # 클라이언트에서 회원가입창 닫을 시 return
            con.close()
            break

        if type == 'stu':  # 학생/선생 table 열어서 id 가져옴
            c.execute("SELECT ID FROM studentTBL")
        elif type == 'tea':
            c.execute("SELECT ID FROM teacherTBL")
        else:
            print('type error in sign_up')
            con.close()
            return
        for row in c:  # id 중복시 NO send
            if check_id in row:
                send_clnt_msg(clnt_sock, '@sign_up NO')
                check = 1
                break
        if check == 1:
            continue
        send_clnt_msg(clnt_sock, '@sign_up OK')  # 중복 아닐시 OK sende

        user_data = recv_clnt_msg(clnt_sock)  # id포함 회원가입 데이터 받아옴(구분자 : /)
        if user_data == 'exit':
            con.close()
            return
        user_data = user_data.split('/')
        lock.acquire()
        if type == 'stu':  # 학생/선생 맞춰서 table에 데이터 저장
            c.executemany(
                "INSERT INTO studentTBL(ID, PW, Name) VALUES(?, ?, ?)", (user_data,))
        elif type == 'tea':
            c.executemany(
                "INSERT INTO teacherTBL(ID, PW, Name) VALUES(?, ?, ?)", (user_data,))
        else:
            print('type error2 in sign_up')
            con.close()
            return
        con.commit()
        con.close()
        lock.release()
        return


# 로그인
def log_in(clnt_num, log_in_data):
    con, c = get_DBcursor()
    clnt_sock = clnt_imfor[clnt_num][0]
    type = clnt_imfor[clnt_num][2]
    log_in_data = log_in_data.split('/')  # log_in_data = 'log_in/ID/PW'
    check_id = log_in_data[1]
    check_pw = log_in_data[2]

    if type == 'stu':  # table에서 id 가져오기
        c.execute('SELECT PW FROM studentTBL WHERE ID=?', (check_id,))
    elif type == 'tea':
        c.execute('SELECT PW FROM teacherTBL WHERE ID=?', (check_id,))
    else:
        print('type error in log_in')
        con.close()
        return
    pw = c.fetchone()
    if not pw:  # 해당 id 없을시 @ID error
        send_clnt_msg(clnt_sock, '@log_in ID error')
        con.close()
        return
    else:  # 해당 id에 대한 pw 일치 시 @sucess send 및 clnt_imfor 갱신
        if (check_pw,) == pw:
            send_clnt_msg(clnt_sock, '@log_in sucess')
            if type == 'stu':
                c.execute('SELECT Point FROM studentTBL WHERE ID=?', (check_id,))
                point = c.fetchone()
                point = ''.join(map(str, point))
                send_clnt_msg(clnt_sock, ('@point ' + point))
            clnt_imfor[clnt_num][1] = check_id
            clnt_imfor[clnt_num][3] = 1
            print('login %s, %s' % (type, check_id))
            con.close()
        else:  # id는 있지만 pw 불일치시 @PW error
            send_clnt_msg(clnt_sock, '@log_in PW error')
            con.close()
    return


# QnA
def QnA_ctrl_func(clnt_num):
    con, c = get_DBcursor()
    type = clnt_imfor[clnt_num][2]
    if type == 'stu':
        c.execute('SELECT * FROM QnATBL')
        rows = c.fetchall()
        if not c:  # 등록된 질문 없을 시 X send
            send_clnt_msg(clnt_imfor[clnt_num][0], '@QnA empty')
        else:  # 질문 등록돼있으면 리스트 다 보내줌
            for row in rows:
                row = list(row)
                row[0] = str(row[0])
                row = '/'.join(row)
                send_clnt_msg(clnt_imfor[clnt_num][0], ('@QnA ' + row))
            send_clnt_msg(clnt_imfor[clnt_num][0], '@QnA done')  # 모든 질문 다 보내주면 완료됐다고 보내줌
        while True:  # 클라이언트에서 quit 보내기 전 까지 계속 질문 받음
            msg = recv_clnt_msg(clnt_imfor[clnt_num][0])
            if msg == '@exit':
                con.close()
                return
            else:
                msg = msg.split('/')
                c.executemany('INSERT INTO QnATBL(ID, Date, Question) VALUES(?, ?, ?)', (msg,))
                con.commit()
                c.execute('SELECT * FROM QnATBL')
                rows = c.fetchall()
                for row in rows:
                    row = list(row)
                    row[0] = str(row[0])
                    row = '/'.join(row)
                    send_clnt_msg(clnt_imfor[clnt_num][0], ('@QnA ' + row))
                send_clnt_msg(clnt_imfor[clnt_num][0], '@QnA done')
    elif type == 'tea':
        c.execute('SELECT * FROM QnATBL')
        rows = c.fetchall()
        if not c:  # 등록된 질문 없을 시 X send
            send_clnt_msg(clnt_imfor[clnt_num][0], '@QnA empty')
            con.close()
            return
        else:
            for row in rows:
                row = list(row)
                row[0] = str(row[0])
                row = '/'.join(row)
                send_clnt_msg(clnt_imfor[clnt_num][0], ('@QnA ' + row))
            send_clnt_msg(clnt_imfor[clnt_num][0], '@QnA done')
        while True:
            msg = recv_clnt_msg(clnt_imfor[clnt_num][0])
            if msg == '@exit':
                con.close()
                break
            else:
                answer = msg.split('/')
                num = int(answer[0])
                c.execute('UPDATE QnATBL SET Answer=? WHERE No=?', (answer[1], num))
                c.execute('SELECT * FROM QnATBL')
                rows = c.fetchall()
                for row in rows:
                    row = list(row)
                    row[0] = str(row[0])
                    row = '/'.join(row)
                    send_clnt_msg(clnt_imfor[clnt_num][0], ('@QnA ' + row))
                send_clnt_msg(clnt_imfor[clnt_num][0], '@QnA done')
                con.commit()
    else:
        print('type error in QA')
        con.close()
        return
    con.close()
    return


# 문제 리스트 보내는 함수
def send_questions(clnt_num, question):  # 문제출제 함수
    question = question.split('/')
    question.remove('list_q')
    con, c = get_DBcursor()

    c.execute('SELECT * FROM QuizTBL WHERE Subject=?', (question[0],))
    rows = c.fetchall()  # db에 있는 특정 과목 리스트 가져옴
    if not rows:  # 없을 시 비어있다고 보내줌
        send_clnt_msg(clnt_imfor[clnt_num][0], '@list_q empty')
    else:
        rows = list(rows)
        for row in rows:  # 문제 데이터 다 보내주기
            row = list(row)
            row[0] = str(row[0])
            row[4] = str(row[4])
            row[5] = str(row[5])
            row = '/'.join(row)
            send_clnt_msg(clnt_imfor[clnt_num][0], ('@list_q ' + row))
    send_clnt_msg(clnt_imfor[clnt_num][0], '@list_q done')  # 다 보내면 done 송신
    if clnt_imfor[clnt_num][2] == 'stu':
        msg = recv_clnt_msg(clnt_imfor[clnt_num][0])
        print(msg)
        if msg == 'exit':
            con.close()
            return
        else:
            hst_data = msg.split('/')
            hst_data[3] = int(hst_data[3])
            print(hst_data)


            c.executemany("INSERT INTO historyTBL(ID, Subject, Data, Score) VALUES(?, ?, ?, ?)", (hst_data,))
            con.commit()
            c.execute('SELECT Point FROM studentTBL WHERE ID=?', (hst_data[0],))
            score = c.fetchone()
            score = list(score)
            print(score)
            score[0] += hst_data[3]
            c.execute('UPDATE studentTBL SET Point=? WHERE ID=?', (score[0], hst_data[0]))
            con.commit()
            quiz_data = eval(hst_data[2])
            for k in quiz_data:
                c.execute('SELECT Solving_count, Correct_count FROM quizTBL WHERE No=?', (k,))
                row = c.fetchone()
                row = list(row)
                row[0] += 1
                if quiz_data[k] == 1:
                    row[1] += 1
                c.execute('UPDATE quizTBL SET Solving_count=?, Correct_count=? WHERE No=?', (row[0], row[1], k))
                con.commit()
    con.close()
    return


# DB에 문제등록
def set_question(clnt_num, data):
    data = data.split('/')
    data.remove('set_q')
    con, c = get_DBcursor()
    if clnt_imfor[clnt_num][2] != 'tea':  # 선생 아니면 문제출제 불가 예외처리
        print('student cant set questions')
        con.close()
        return
    else:
        lock.acquire()
        c.executemany(
            "INSERT INTO quizTBL(Subject, Quiz, Answer) VALUES(?, ?, ?)", (data,))
        con.commit()
        con.close()
        lock.release()
    return


# 채팅 주고받기
def get_chat(clnt_num):
    con, c = get_DBcursor()
    type = clnt_imfor[clnt_num][2]
    if type == 'stu':  # 학생/선생 table 열어서 id 가져옴
        c.execute("SELECT Name FROM studentTBL WHERE ID=?", (clnt_imfor[clnt_num][1],))
    elif type == 'tea':
        c.execute("SELECT Name FROM teacherTBL WHERE ID=?", (clnt_imfor[clnt_num][1],))
    else:
        print('type error in get_chat')
        return
    clnt_name = c.fetchone()
    clnt_name = ''.join(clnt_name)

    while True:
        msg = recv_clnt_msg(clnt_imfor[clnt_num][0])  # 채팅중인 클라이언트들 메세지 수신
        if msg == '@exit':  # exit 수신시 나갔다고 상대방에게 보내주고 채팅모드 off
            for i in range(0, clnt_cnt):
                if clnt_imfor[clnt_num][3] == clnt_imfor[i][3]:
                    send_clnt_msg(clnt_imfor[i][0], ('@chat [%s]님이 채팅방을 나갔습니다.' % clnt_name))
            clnt_imfor[clnt_num][3] = 1
            break
        else:  # 송신한 클라이언트와 상대방에게 메세지 보내기
            msg = msg.replace('@chat ', ('@chat [%s] ' % clnt_name))
            for i in range(0, clnt_cnt):
                if clnt_imfor[clnt_num][3] == clnt_imfor[i][3]:
                    send_clnt_msg(clnt_imfor[i][0], msg)
    con.close()
    return


# 채팅 요청 보내고 채팅모드 on
def set_chat_state(clnt_num, name):
    global room_num
    if clnt_imfor[clnt_num][3] != 1:  # 채팅중일시 예외처리
        get_chat(clnt_num)
    con, c = get_DBcursor()
    name = name.replace('chat/', '')
    send_clnt_msg(clnt_imfor[clnt_num][0], '@chat 서버메세지 : 연결중입니다.')
    if clnt_imfor[clnt_num][2] == 'stu':  # 학생이 채팅요청 했을 경우
        c.execute('SELECT ID FROM teacherTBL WHERE Name=?', (name,))
        tea_id = c.fetchone()
        if not tea_id:  # 이름 없을 시 에러 표시
            print('name error')
            con.close()
            return
        tea_id = ''.join(tea_id)
        for i in range(0, clnt_cnt):  # 선생님에게 invite 송신
            if clnt_imfor[i][2] == 'tea' and clnt_imfor[i][1] == tea_id and clnt_imfor[i][3] == 1:
                send_clnt_msg(clnt_imfor[i][0], '@invite')
                msg = recv_clnt_msg(clnt_imfor[i][0])
                if msg == '@invite OK':  # 수락했을 경우 채팅모드on
                    clnt_imfor[clnt_num][3] = room_num
                    clnt_imfor[i][3] = room_num
                    room_num = room_num + 1
                    get_chat(clnt_num)
                    con.close()
                    return
                elif msg == '@chat NO':
                    send_clnt_msg(clnt_imfor[clnt_num][0], '@invite NO')
                    con.close()
                    return
    elif clnt_imfor[clnt_num][2] == 'tea':
        c.execute('SELECT ID FROM studentTBL WHERE Name=?', (name,))
        stu_id = c.fetchone()
        if not stu_id:
            print('name error')
            con.close()
            return
        stu_id = ''.join(stu_id)
        for i in range(0, clnt_cnt):
            if clnt_imfor[i][2] == 'stu' and clnt_imfor[i][1] == stu_id and clnt_imfor[i][3] == 1:
                send_clnt_msg(clnt_imfor[i][0], '@invite')
                msg = recv_clnt_msg(clnt_imfor[i][0])
                if msg == '@invite OK':
                    clnt_imfor[clnt_num][3] = room_num
                    clnt_imfor[i][3] = room_num
                    room_num = room_num + 1
                    get_chat(clnt_num)
                    con.close()
                    return
                elif msg == '@chat NO':
                    send_clnt_msg(clnt_imfor[clnt_num][0], '@invite NO')
                    con.close()
                    return
    else:
        print('type error in set_chat_state')
        con.close()
        return


# 접속자명단 보내는 함수
def send_user_list(clnt_num):
    con, c = get_DBcursor()
    name_list = []
    if clnt_imfor[clnt_num][2] == 'tea':  # 리스트 요청한 게 선생님일 경우
        for i in range(0, clnt_cnt):  # 접속중인 학생들 이름 찾아서 name_list에 등록
            if clnt_imfor[i][2] == 'stu' and clnt_imfor[i][3] == 1:
                c.execute('SELECT Name FROM studentTBL WHERE ID=?', (clnt_imfor[i][1],))
                name_data = c.fetchone()
                name_data = ''.join(name_data)
                name_list.append(name_data)
    elif clnt_imfor[clnt_num][2] == 'stu':
        for i in range(0, clnt_cnt):
            if clnt_imfor[i][2] == 'tea' and clnt_imfor[i][3] == 1:
                c.execute('SELECT Name FROM teacherTBL WHERE ID=?', (clnt_imfor[i][1],))
                name_data = c.fetchone()
                name_data = ''.join(name_data)
                name_list.append(name_data)
    else:
        print('type error in send_list')
        con.close()
        return
    if len(name_list) == 0:  # 접속자 없을 경우 없다고 송신
        send_clnt_msg(clnt_imfor[clnt_num][0], '@member empty')
    else:  # 있으면 리스트를 문자열로 바꿔서 송신
        send_data = '/'.join(name_list)
        send_clnt_msg(clnt_imfor[clnt_num][0], ('@member ' + send_data))
    con.close()
    return


def send_result(clnt_num, sub):
    con, c = get_DBcursor()
    sub = sub.split('/')
    c.execute('SELECT * FROM quizTBL WHERE Subject=?', (sub[1],))
    # c.execute('SELECT * FROM quizTBL')
    rows = c.fetchall()
    if not rows:
        send_clnt_msg(clnt_imfor[clnt_num][0], '@graph empty')
        con.close()
        return
    else:
        rows = list(rows)
        for row in rows:
            data = list(row)
            if data[5] == 0:
                data.append('0')
            else:
                per = (row[5] / row[4]) * 100
                data.append(str(per))
            data[0] = str(data[0])
            data[4] = str(data[4])
            data[5] = str(data[5])
            print(data)
            send_data = '/'.join(data)
            send_clnt_msg(clnt_imfor[clnt_num][0], ('@graph ' + send_data))
        send_clnt_msg(clnt_imfor[clnt_num][0], '@graph done')
        con.close()
        return


def send_mark(clnt_num):
    con, c = get_DBcursor()
    send_list = []
    c.execute('SELECT Name, ID FROM studentTBL')
    rows = c.fetchall()
    rows = list(rows)
    for row in rows:
        row = list(row)
        send_list.append(row[0])
    rows = '/'.join(send_list)
    send_clnt_msg(clnt_imfor[clnt_num][0], ('@mark ' + rows))
    while True:
        msg = recv_clnt_msg(clnt_imfor[clnt_num][0])
        if msg == 'exit':
            con.close()
            return
        c.execute('SELECT * FROM historyTBL WHERE ID=(SELECT ID FROM studentTBL WHERE Name=?)', (msg,))
        rows = c.fetchall()
        if not rows:
            send_clnt_msg(clnt_imfor[clnt_num][0], '@mark empty')
        else:
            for row in rows:
                row = list(row)
                row[3] = str(row[3])
                send_data = '/'.join(row)
                print(send_data)
                send_clnt_msg(clnt_imfor[clnt_num][0], ('@result ' + send_data))
            send_clnt_msg(clnt_imfor[clnt_num][0], '@result done')


# 상황에 맞는 함수 호출해주는 함수
def call_func(clnt_num, instruction):
    if instruction == 'sign_up':
        sign_up(clnt_num)
    elif instruction.startswith('log_in'):
        log_in(clnt_num, instruction)
    elif instruction.startswith('list_q'):
        send_questions(clnt_num, instruction)
    elif instruction == 'QnA':
        QnA_ctrl_func(clnt_num)
    elif instruction.startswith('chat'):
        set_chat_state(clnt_num, instruction)
    elif instruction == 'member':
        send_user_list(clnt_num)
    elif instruction.startswith('set_q'):
        set_question(clnt_num, instruction)
    elif instruction.startswith('graph'):
        send_result(clnt_num, instruction)
    elif instruction == 'mark':
        send_mark(clnt_num)
    else:
        return


# 클라이언트에게서 오는 메세지 대기
def handle_clnt(clnt_sock):
    lock.acquire()
    for i in range(0, clnt_cnt):  # clnt_imfor에 해당 클라이언트가 몇 번째에 있는지 추출
        if clnt_imfor[i][0] == clnt_sock:
            clnt_num = i
            break
    lock.release()

    while True:
        clnt_msg = recv_clnt_msg(clnt_sock)
        if clnt_msg == '@exit' or not clnt_msg:  # 클라이언트 연결 끊길 시
            lock.acquire()
            delete_imfor(clnt_sock)
            clnt_sock.close()
            lock.release()
            break

        print(clnt_msg)
        if clnt_msg.startswith('@'):  # 특정 기능 실행 시 @ 붙여서 받음
            clnt_msg = clnt_msg.replace('@', '')
            call_func(clnt_num, clnt_msg)  # 명령어 함수 호출하는 함수
        else:
            continue


# main
if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))
    sock.listen(5)

    while True:
        clnt_sock, addr = sock.accept()
        clnt_msg = recv_clnt_msg(clnt_sock)

        lock.acquire()
        clnt_imfor.insert(clnt_cnt, [clnt_sock, '!log_in', clnt_msg, 0])  # 클라이언트 접속시 clnt_imfor에 정보 저장
        clnt_cnt += 1
        print('connect client, type %s' % clnt_msg)
        lock.release()

        t = threading.Thread(target=handle_clnt, args=(clnt_sock,))  # 클라이언트별로 스레드 할당
        t.start()