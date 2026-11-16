import csv
import json
import math
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from engine import MAP_SIZE_M, Parameters, calculate, distance, project_to_route
from strategy import evaluate
from empirical import assess_route, recorded_summary
from maps import MAPS, PROFILES
from guidance import make_guidance
from map_assets import cached_path, read_metadata, update_map
from app_update import VERSION, check_update, stage_update, start_install

BASE = Path(__file__).resolve().parent

class DropAssistant(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f'PUBG Drop Assistant v{VERSION} — OFFLINE CALCULATOR')
        self.geometry('1150x790')
        self.minsize(900, 650)
        self.route_start = None
        self.route_end = None
        self.target = None
        self.image = None
        self.image_path = ''
        self.map_name = tk.StringVar(value='Erangel')
        self.mode = tk.StringVar(value='start')
        self.strategy_mode = tk.StringVar(value='empirical')
        self.preferred = tk.StringVar(value='750')
        self.terrain = tk.StringVar(value='49')
        self.speed = tk.StringVar(value='100')
        self.descent = tk.StringVar(value='35')
        self.glide = tk.StringVar(value='38')
        self.status = tk.StringVar(value='지도에서 비행기 시작점 → 끝점 → 착륙 목표를 클릭하세요.')
        self.video_path = tk.StringVar()
        self.template_rect = tk.StringVar(value='1200,600,45,45')
        self.search_rect = tk.StringVar(value='0,0,2560,1440')
        self.threshold = tk.StringVar(value='0.65')
        self.interval = tk.StringVar(value='5')
        self._build()
        self._load_cached_map()
        self._draw()
        self.after(700, self._offer_initial_download)
        self.after(2000, self.check_program_update)

    def _build(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill='x')
        ttk.Label(top, text=f'PUBG DROP ASSISTANT v{VERSION} | OFFLINE CALCULATOR', font=('Segoe UI', 13, 'bold')).pack(side='left')
        ttk.Combobox(top, textvariable=self.map_name, values=list(MAPS), width=17, state='readonly').pack(side='left', padx=12)
        self.map_name.trace_add('write', self.on_map_change)
        ttk.Button(top, text='프로그램 업데이트', command=lambda: self.check_program_update(manual=True)).pack(side='right', padx=4)
        ttk.Button(top, text='수동 이미지', command=self.load_map).pack(side='right', padx=4)
        ttk.Button(top, text='지도 업데이트 확인', command=self.update_selected_map).pack(side='right', padx=4)
        ttk.Button(top, text='설정 불러오기', command=self.load_project).pack(side='right', padx=4)
        ttk.Button(top, text='설정 저장', command=self.save_project).pack(side='right', padx=4)
        outer = ttk.PanedWindow(self, orient='horizontal')
        outer.pack(fill='both', expand=True, padx=10, pady=5)
        left = ttk.Frame(outer)
        right = ttk.Frame(outer, padding=10)
        outer.add(left, weight=3)
        outer.add(right, weight=2)
        self.canvas = tk.Canvas(left, background='#24382d', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Button-1>', self.click_map)
        self.canvas.bind('<Configure>', lambda _: self._draw())
        modes = ttk.LabelFrame(right, text='1. 좌표 지정', padding=8)
        modes.pack(fill='x', pady=4)
        for val, title in [('start', '비행기 시작점'), ('end', '비행기 끝점'), ('target', '착륙 목표')]:
            ttk.Radiobutton(modes, text=title, variable=self.mode, value=val).pack(anchor='w')
        ttk.Button(modes, text='좌표 초기화', command=self.clear).pack(fill='x', pady=4)
        physics = ttk.LabelFrame(right, text='2. 계산 모드 (실측 1회 기록 참고)', padding=8)
        physics.pack(fill='x', pady=4)
        for label, var in [('비행기 속도 (m/s)', self.speed), ('기본 하강 시간 (초)', self.descent), ('수평 이동 속도 (m/s)', self.glide)]:
            line = ttk.Frame(physics)
            line.pack(fill='x', pady=2)
            ttk.Label(line, text=label).pack(side='left')
            ttk.Entry(line, textvariable=var, width=10).pack(side='right')
        ttk.Radiobutton(physics, text='커뮤니티 전략 비교 (실험적)', variable=self.strategy_mode, value='community').pack(anchor='w')
        ttk.Radiobutton(physics, text='기존 단순 추정 모델', variable=self.strategy_mode, value='legacy').pack(anchor='w')
        ttk.Radiobutton(physics, text='v0.4 지도별 커뮤니티 기준 / 기하학적 후보', variable=self.strategy_mode, value='empirical').pack(anchor='w')
        for label, var in [('선호 이탈 거리 (m)',self.preferred),('목표 지형 절대 고도 (m)',self.terrain)]:
            line=ttk.Frame(physics); line.pack(fill='x',pady=2)
            ttk.Label(line,text=label).pack(side='left')
            ttk.Entry(line,textvariable=var,width=9).pack(side='right')
        ttk.Label(physics,text='실측은 에란겔 1회만. 지도별 낙하 가이드는 검증된 최적 제어가 아닌 참고값입니다.',wraplength=330).pack(anchor='w')
        ttk.Button(physics, text='추천 이탈 지점 계산', command=self.compute).pack(fill='x', pady=5)
        self.result = tk.Text(right, height=15, width=38, wrap='word', state='disabled', font=('Consolas', 10))
        self.result.pack(fill='x', pady=4)
        video = ttk.LabelFrame(right, text='3. 녹화 영상 분석 (게임 실시간 연결 없음)', padding=8)
        video.pack(fill='both', expand=True, pady=4)
        line = ttk.Frame(video)
        line.pack(fill='x')
        ttk.Entry(line, textvariable=self.video_path).pack(side='left', fill='x', expand=True)
        ttk.Button(line, text='영상 선택', command=self.choose_video).pack(side='right')
        for label, var in [('아이콘 영역 x,y,w,h', self.template_rect), ('탐색 영역 x,y,w,h', self.search_rect), ('최소 일치 점수 (0~1)', self.threshold), ('분석 간격 (프레임)', self.interval)]:
            ttk.Label(video, text=label).pack(anchor='w', pady=(5,0))
            ttk.Entry(video, textvariable=var).pack(fill='x')
        ttk.Button(video, text='첫 프레임 미리보기 / 영역 선택', command=self.preview_video).pack(fill='x', pady=(8,2))
        ttk.Button(video, text='녹화 영상 추적 → CSV', command=self.analyze_video).pack(fill='x', pady=2)
        ttk.Label(video, text='주의: 지도 화면이 열려 있고 아이콘 크기가 일정한 영상에 적합합니다.', wraplength=310).pack(anchor='w')
        ttk.Label(self, textvariable=self.status, padding=8).pack(fill='x')

    def map_size(self):
        return MAPS[self.map_name.get()]

    def on_map_change(self, *_):
        self.route_start=self.route_end=self.target=None
        self.recommendation=None
        self.image=None
        self.image_path=''
        self._load_cached_map()
        self.preferred.set(str(PROFILES[self.map_name.get()]['distance']))
        self.status.set(f'{self.map_name.get()} 지도 선택 · 캐시 지도 자동 표시 · 업데이트는 버튼으로 확인')
        self._draw()
        if self.image is None:
            self.after(150, self._offer_initial_download)

    def dims(self):
        w, h = max(self.canvas.winfo_width(), 300), max(self.canvas.winfo_height(), 300)
        side = max(10, min(w-24, h-24))
        return (w-side)/2, (h-side)/2, side

    def to_pixel(self, point):
        x0, y0, side = self.dims()
        return x0 + point[0]/self.map_size()*side, y0 + point[1]/self.map_size()*side

    def from_pixel(self, x, y):
        x0, y0, side = self.dims()
        if not (x0 <= x <= x0+side and y0 <= y <= y0+side):
            return None
        return ((x-x0)/side*self.map_size(), (y-y0)/side*self.map_size())

    def click_map(self, event):
        p = self.from_pixel(event.x, event.y)
        if p is None:
            return
        mode = self.mode.get()
        if mode == 'start':
            self.route_start = p
            self.mode.set('end')
        elif mode == 'end':
            self.route_end = p
            self.mode.set('target')
        else:
            self.target = p
        self._draw()
        self.status.set(f'{mode}: ({p[0]:.0f}, {p[1]:.0f}) m')

    def _draw(self):
        self.canvas.delete('all')
        x0, y0, side = self.dims()
        self.canvas.create_rectangle(x0,y0,x0+side,y0+side,fill='#304d3c',outline='#a0b4a0',width=2)
        if self.image:
            try:
                from PIL import ImageTk
                self._tk_image = ImageTk.PhotoImage(self.image.resize((int(side), int(side))))
                self.canvas.create_image(x0,y0,anchor='nw',image=self._tk_image)
            except ImportError:
                pass
        for i in range(1,8):
            v = i*side/8
            self.canvas.create_line(x0+v,y0,x0+v,y0+side,fill='#b6c6bb',dash=(2,5))
            self.canvas.create_line(x0,y0+v,x0+side,y0+v,fill='#b6c6bb',dash=(2,5))
        if self.route_start and self.route_end:
            a,b=self.to_pixel(self.route_start),self.to_pixel(self.route_end)
            self.canvas.create_line(*a,*b,fill='#6ecbff',width=3,dash=(9,4))
        for point,color,name in [(self.route_start,'#55e1fc','START'),(self.route_end,'#55e1fc','END'),(self.target,'#ffcc42','TARGET')]:
            if point:
                x,y=self.to_pixel(point)
                self.canvas.create_oval(x-6,y-6,x+6,y+6,fill=color,outline='#101820',width=2)
                self.canvas.create_text(x+9,y-12,text=name,anchor='w',fill='white',font=('Segoe UI',10,'bold'))
        if hasattr(self,'recommendation') and self.recommendation:
            x,y=self.to_pixel(self.recommendation['exit'])
            self.canvas.create_oval(x-9,y-9,x+9,y+9,outline='#ff5969',width=3)
            self.canvas.create_text(x+12,y+14,text='ESTIMATED EXIT',anchor='w',fill='#ff9aa6')

    def clear(self):
        self.route_start=self.route_end=self.target=None
        self.recommendation=None
        self.mode.set('start')
        self._draw()

    def compute(self):
        if not all((self.route_start,self.route_end,self.target)):
            messagebox.showwarning('좌표 필요','시작점, 끝점, 착륙 목표를 지정하세요.')
            return
        try:
            p=Parameters(float(self.speed.get()),float(self.descent.get()),float(self.glide.get()))
            if self.strategy_mode.get()=='legacy':
                r=calculate(self.route_start,self.route_end,self.target,p)
            elif self.strategy_mode.get()=='community':
                r=evaluate(self.route_start,self.route_end,self.target,p.plane_speed_mps)
            else:
                preferred=float(self.preferred.get())
                if preferred <= 0 or preferred > self.map_size():
                    raise ValueError('선호 이탈 거리는 0보다 크고 지도 한 변 이하이어야 합니다.')
                r=assess_route(self.route_start,self.route_end,self.target,p.plane_speed_mps,preferred,float(self.terrain.get()))
        except ValueError as e:
            messagebox.showerror('입력 오류',str(e))
            return
        if self.strategy_mode.get()=='empirical':
            chosen=r['recommended']
            self.recommendation=chosen
            self._draw()
            kind='최단 접근점 (선호 반경과 교차하지 않음)' if chosen['fallback'] else '선호 거리 교차점'
            lines=[f'경로-목표 최단거리: {r["nearest_distance_m"]:.0f}m',
                   f'추천 후보: {kind}',f'이탈-목표 거리: {chosen["distance_m"]:.0f}m',
                   f'비행기 시작→이탈: {chosen["plane_wait_s"]:.1f}초 (입력 비행기 속도 가정)',
                   f'이탈 좌표: ({chosen["exit"][0]:.0f}, {chosen["exit"][1]:.0f})m',
                   '실측 기준 궤적: 39초 / 수평 누적 1125m (에란겔 전용)',
                   'Shift 시작 23초 / 낙하산 전개 26초',
                   '실측 HUD 최대 속도 232km/h',
                   '예상 착륙 시간: 산출 불가 (교차 전략 검증 전)',
                   '낙하 고도/속도: 실측 궤적과 동일한 조작일 때만 참고',
                   '',r['warning']]
            if not chosen['terrain_matches_recording']:
                lines.append('주의: 목표 지형 고도가 실측 착륙고도 49m와 다릅니다.')
            lines.extend(['', '--- 단계별 낙하 가이드 ---', make_guidance(self.map_name.get(),chosen['distance_m'],float(self.terrain.get()))])
            self.show_result('\n'.join(lines))
            return
        if self.strategy_mode.get()=='community':
            chosen=r['recommended']
            if not chosen:
                self.recommendation=None
                self._draw()
                self.show_result(f'비행 경로와 목표 최단거리: {r["nearest_distance_m"]:.0f}m\n현재 전략들의 실험적 도달범위 밖입니다.\n수동 장거리 활공 검토가 필요합니다.')
                return
            self.recommendation=chosen
            self._draw()
            lines=[f'경로와 목표 최단거리: {r["nearest_distance_m"]:.0f}m',f'실험적 추천: {chosen["strategy"]}',f'이탈 좌표: ({chosen["exit"][0]:.0f}, {chosen["exit"][1]:.0f})m',f'이탈-목표 거리: {chosen["target_distance_m"]:.0f}m',f'급강하 전환 기준: {chosen["dive_transition_m"]:.0f}m','', '다른 전략 후보:']
            lines += [f'- {c["strategy"]}: {c["target_distance_m"]:.0f}m 이탈 / 비교점수 {c["score_seconds"]:.1f}' for c in r['candidates']]
            lines += ['',r['warning']]
            self.show_result('\n'.join(lines))
            return
        self.recommendation=r
        self._draw()
        x,y=r['exit']
        self.show_result(f'추천 이탈 위치: ({x:.0f}, {y:.0f}) m\n경로 진행률: {r["fraction"]*100:.1f}%\n비행 시작 → 이탈: {r["plane_seconds"]:.1f}초\n이탈 → 착륙 추정: {r["flight_seconds"]:.1f}초\n총 예상 시간: {r["total_seconds"]:.1f}초\n이탈 위치 → 목표: {r["target_distance_m"]:.0f}m\n\n※ 단순 추정 모델입니다. 실제 최적 착륙을 보장하지 않습니다.')

    def show_result(self, msg):
        self.result.configure(state='normal')
        self.result.delete('1.0','end')
        self.result.insert('1.0',msg)
        self.result.configure(state='disabled')

    def _load_cached_map(self):
        path = cached_path(self.map_name.get())
        if path.is_file():
            try:
                from PIL import Image
                with Image.open(path) as im:
                    self.image = im.convert('RGB')
                self.image_path = str(path)
                return True
            except Exception:
                self.image = None
        return False

    def _offer_initial_download(self):
        if self.image is not None:
            return
        if messagebox.askyesno('지도 이미지 자동 다운로드',
            '선택한 지도의 로컬 이미지가 없습니다.\nPUBG 공식 API 에셋 저장소에서 다운로드할까요?\n\n인터넷 연결이 필요하며, 공식 에셋도 최신 게임 패치와 다를 수 있습니다.'):
            self.update_selected_map()

    def check_program_update(self, manual=False):
        if getattr(self, '_checking_update', False):
            return
        self._checking_update = True
        def worker():
            try:
                info = check_update()
                self.after(0, lambda: self._update_check_done(info, manual))
            except Exception as exc:
                msg = str(exc)
                self.after(0, lambda: self._update_check_failed(msg, manual))
        threading.Thread(target=worker, daemon=True).start()

    def _update_check_failed(self, msg, manual):
        self._checking_update = False
        if manual:
            messagebox.showwarning('프로그램 업데이트 확인 실패', msg)

    def _update_check_done(self, info, manual):
        self._checking_update = False
        if not info:
            if manual:
                messagebox.showinfo('프로그램 업데이트', '현재 최신 버전이거나 배포된 업데이트가 없습니다.')
            return
        notes = info.get('notes', '')[:700]
        if not messagebox.askyesno('프로그램 업데이트',
                f'새 버전 {info["version"]}이 있습니다.\n현재 버전: v{VERSION}\n\n{notes}\n\n다운로드하고 설치할까요?'):
            return
        self.status.set(f'{info["version"]} 다운로드 및 무결성 확인 중...')
        def worker():
            try:
                new_exe, updater_exe = stage_update(info)
                self.after(0, lambda: self._install_program_update(new_exe, updater_exe))
            except Exception as exc:
                msg = str(exc)
                self.after(0, lambda: messagebox.showerror('프로그램 업데이트 실패', msg))
        threading.Thread(target=worker, daemon=True).start()

    def _install_program_update(self, new_exe, updater_exe):
        try:
            start_install(new_exe, updater_exe)
        except Exception as exc:
            messagebox.showerror('프로그램 업데이트 실패', str(exc))
            return
        self.destroy()

    def update_selected_map(self):
        name = self.map_name.get()
        self.status.set(f'{name} 공식 지도 버전 확인 및 다운로드 중...')
        def worker():
            try:
                path, state = update_map(name)
                self.after(0, lambda: self._map_update_done(name, path, state))
            except Exception as e:
                msg = str(e)
                self.after(0, lambda: self._map_update_failed(name, msg))
        threading.Thread(target=worker, daemon=True).start()

    def _map_update_done(self, name, path, state):
        if name == self.map_name.get():
            self._load_cached_map()
            self._draw()
        labels = {'downloaded':'다운로드 완료', 'updated':'새 버전으로 교체 완료', 'current':'현재 공식 저장소 버전과 동일'}
        meta = read_metadata(name)
        self.status.set(f'{name}: {labels.get(state, state)} · {meta.get("filename", "")}; 게임 최신 패치 일치 여부는 별도 확인 필요')

    def _map_update_failed(self, name, msg):
        self.status.set(f'{name}: 다운로드 실패. 기존 캐시/수동 지도를 유지합니다.')
        messagebox.showwarning('지도 업데이트 실패', msg)

    def load_map(self):
        path=filedialog.askopenfilename(filetypes=[('Images','*.png *.jpg *.jpeg *.webp')])
        if not path:return
        try:
            from PIL import Image
            self.image=Image.open(path).convert('RGB')
            self.image_path=path
            self._draw()
        except Exception as e:
            messagebox.showerror('지도 오류',f'Pillow 설치 또는 이미지 확인이 필요합니다:\n{e}')

    def save_project(self):
        path=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('JSON','*.json')])
        if not path:return
        data={'map':self.map_name.get(),'start':self.route_start,'end':self.route_end,'target':self.target,'plane_speed':self.speed.get(),'descent':self.descent.get(),'glide':self.glide.get(),'image_path':self.image_path,'strategy_mode':self.strategy_mode.get(),'preferred_m':self.preferred.get(),'terrain_altitude_m':self.terrain.get()}
        Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
        self.status.set('프로젝트 저장 완료')

    def load_project(self):
        path=filedialog.askopenfilename(filetypes=[('JSON','*.json')])
        if not path:return
        try:
            d=json.loads(Path(path).read_text(encoding='utf-8'))
            self.map_name.set(d.get('map','Erangel') if d.get('map','Erangel') in MAPS else 'Erangel')
            self.route_start=d.get('start')
            self.route_end=d.get('end')
            self.target=d.get('target')
            self.speed.set(d.get('plane_speed','100'))
            self.descent.set(d.get('descent','35'))
            self.glide.set(d.get('glide','38'))
            self.strategy_mode.set(d.get('strategy_mode','empirical'))
            self.preferred.set(d.get('preferred_m','750'))
            self.terrain.set(d.get('terrain_altitude_m','49'))
            self.image=None
            self.image_path=d.get('image_path','')
            if self.image_path and Path(self.image_path).exists():
                from PIL import Image
                self.image=Image.open(self.image_path).convert('RGB')
            else:
                self._load_cached_map()
            self.recommendation=None
            self._draw()
        except Exception as e:
            messagebox.showerror('불러오기 실패',str(e))

    def choose_video(self):
        path=filedialog.askopenfilename(filetypes=[('Video','*.mp4 *.mkv *.avi *.mov'),('All files','*.*')])
        if path:self.video_path.set(path)

    def preview_video(self):
        if not self.video_path.get():
            messagebox.showwarning('영상 필요','먼저 녹화 영상을 선택하세요.')
            return
        try:
            import cv2
            from PIL import Image, ImageTk
            cap=cv2.VideoCapture(self.video_path.get())
            ok,frame=cap.read()
            cap.release()
            if not ok:raise ValueError('첫 프레임을 읽지 못했습니다.')
            rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            preview=tk.Toplevel(self)
            preview.title('첫 프레임 — 드래그: 아이콘 영역 / 우클릭 드래그: 탐색 영역')
            h,w=rgb.shape[:2]
            scale=min(1100/w,750/h,1.0)
            image=Image.fromarray(rgb).resize((int(w*scale),int(h*scale)))
            photo=ImageTk.PhotoImage(image)
            canvas=tk.Canvas(preview,width=image.width,height=image.height)
            canvas.pack()
            canvas.create_image(0,0,image=photo,anchor='nw')
            canvas.image=photo
            state={}
            def begin(event):state['start']=(event.x,event.y)
            def finish(event, target):
                if 'start' not in state:return
                ax,ay=state['start'];bx,by=event.x,event.y
                x,y=int(min(ax,bx)/scale),int(min(ay,by)/scale)
                rw,rh=int(abs(bx-ax)/scale),int(abs(by-ay)/scale)
                if rw>0 and rh>0:target.set(f'{x},{y},{rw},{rh}')
                canvas.create_rectangle(ax,ay,bx,by,outline='#ffcc42' if target==self.template_rect else '#33ddff',width=2)
            canvas.bind('<ButtonPress-1>',begin)
            canvas.bind('<ButtonRelease-1>',lambda e:finish(e,self.template_rect))
            canvas.bind('<ButtonPress-3>',begin)
            canvas.bind('<ButtonRelease-3>',lambda e:finish(e,self.search_rect))
        except Exception as e:
            messagebox.showerror('미리보기 오류',str(e))

    def analyze_video(self):
        if not self.video_path.get():
            messagebox.showwarning('영상 필요','먼저 녹화 영상을 선택하세요.')
            return
        output=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if not output:return
        try:
            template=[int(x.strip()) for x in self.template_rect.get().split(',')]
            search=[int(x.strip()) for x in self.search_rect.get().split(',')]
            if len(template)!=4 or len(search)!=4:raise ValueError('영역은 x,y,w,h 네 숫자여야 합니다')
            interval=int(self.interval.get())
            threshold=float(self.threshold.get())
            if interval<1 or not (0<=threshold<=1):raise ValueError('분석 간격 또는 점수 범위가 잘못됐습니다')
        except ValueError as e:
            messagebox.showerror('입력 오류',str(e))
            return
        self.status.set('녹화 영상 분석 중... (UI는 계속 사용할 수 있습니다)')
        def job():
            try:
                from tracker import track_video
                n,total=track_video(self.video_path.get(),template,search,output,interval,threshold)
                self.after(0,lambda:self.status.set(f'분석 완료: {total}프레임 중 {n}개 위치 기록 → {output}'))
            except Exception as e:
                err=str(e)
                self.after(0,lambda:messagebox.showerror('분석 실패',err))
                self.after(0,lambda:self.status.set('분석 실패'))
        threading.Thread(target=job,daemon=True).start()

if __name__=='__main__':
    DropAssistant().mainloop()
