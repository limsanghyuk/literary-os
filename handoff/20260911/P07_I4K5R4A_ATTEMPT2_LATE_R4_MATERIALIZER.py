from pathlib import Path
BASE=Path('handoff/20260911/i4k5r4a_attempt2/treatment_late_superseding_r3')
OUT=Path('handoff/20260911/i4k5r4a_attempt2/treatment_late_superseding_r4')
OUT.mkdir(parents=True,exist_ok=True)
items={
'P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ07_S31_35_R3_20260911.txt':('P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ07_S31_35_R4_20260911.txt','''\n\n도현은 새 배치표를 무전으로 읽은 뒤 실제 후면선과 객석선을 차례로 바라본다. 준호는 직원 카트 손잡이를 자기 쪽으로 당겨 봉사자 이동선에서 한 뼘 더 떼어놓고, 유정은 프로그램 상자 모서리를 객석선 안으로 맞춘다. 같은 시간에 두 작업이 계속되지만 손과 발이 향하는 방향은 끝까지 갈라져 있다.'''),
'P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ08_S36_40_R3_20260911.txt':('P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ08_S36_40_R4_20260911.txt','''\n\n준호는 시간표 아래 그린 네 사각형 옆에 오늘 실제 사용한 카트 번호와 랙 번호를 작은 글씨로 적는다. 세윤은 퀵체인지 문을 다시 열어 랙 손잡이가 방화문 회전반경 밖에 놓였는지 눈으로 확인하고, 손바닥을 문 가장자리와 랙 사이에 세워 간격을 보여준다. 유정은 접근성 대기선 표지를 접었다가 다시 펼쳐 노란 시험선과 겹치지 않는 위치에 세운다. 도현은 세 사람이 바꾼 위치를 종이에 대신 옮기지 않고, 각자 자기 색 자석을 실제 위치와 같은 순서로 놓게 한다.\n\n그 뒤 준호가 빈 카트를 시험 삼아 후면 대기선에서 방화문 앞까지 천천히 밀어본다. 18:35 검은칸에 해당하는 지점에서는 바퀴를 멈추고 브레이크를 잠근다. 세윤은 의상 랙을 반대편에서 같은 방식으로 한 번 움직였다가 18:34 위치에서 멈춘다. 유정은 관객 대기선을 손으로 짚으며 두 이동물의 끝점 사이에 사람이 지나갈 빈 폭이 남는지 확인한다. 세 작업의 시작과 멈춤이 같은 긴 종이 위 시간표와 실제 바닥에서 동시에 맞아 떨어진다.'''),
'P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ09_S41_45_R3_20260911.txt':('P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ09_S41_45_R4_20260911.txt','''\n\n운영사무실 문을 나설 때 여섯 사람은 동시에 움직이지 않는다. 나경이 먼저 무대 쪽으로, 세윤은 인계실 쪽으로, 기준은 부스 계단으로 갈라진다. 준호와 유정도 각각 후면과 객석으로 방향을 틀고, 도현만 잠시 빈 테이블 앞에 남아 개막시각이 적힌 한 장을 접는다. 판단자료는 각 현장으로 돌아가고 공통시각만 그의 손에 남는다.''')}
for src,(dst,extra) in items.items():
    text=(BASE/src).read_text(encoding='utf-8')
    text=text.replace('SUPERSEDING_R3','SUPERSEDING_R4',1)
    (OUT/dst).write_text(text.rstrip()+extra+'\n',encoding='utf-8')
    print(dst,len((OUT/dst).read_text(encoding='utf-8')))