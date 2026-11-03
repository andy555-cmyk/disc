/* 이생동 장부 엔진 — 화면과 모의실험이 같이 쓴다
   실제: 점포당 월평균 추정매출(서울시 상권분석서비스, 매출÷유사업종 점포 수), 시간대 매출 비중, 최저임금
   가정: 아래 IND·LOC·HOURS·ACT 표의 숫자 전부. IND.mat = 원가·기타 운영비 비율, 업종마다 「그대로 버티기」 판의 서울 동 중앙값이 5년 +3천만 원이 되게 맞춤(모의실험 town_bisect) */
(function(root){
const IND={
 cafe:{nm:"카페",mat:0.53,ent:2500},chicken:{nm:"치킨집",mat:0.56,ent:2800},bunsik:{nm:"분식집",mat:0.58,ent:2200},
 bakery:{nm:"빵집",mat:0.66,ent:3500},hair:{nm:"미용실",mat:0.34,ent:2500},conv:{nm:"편의점",mat:0.7,ent:3000},
 hof:{nm:"호프집",mat:0.7,ent:3000},banchan:{nm:"반찬가게",mat:0.66,ent:1800}};
const LOC={main:{nm:"큰길 1층",sales:1.15,rent:.20},alley:{nm:"골목 1층",sales:.92,rent:.12},up:{nm:"2층",sales:.72,rent:.07}};
/* 시간대 칸: 00-06,06-11,11-14,14-17,17-21,21-24 */
const HOURS={am:{nm:"아침·점심형 (6~17시)",slots:[1,2,3]},day:{nm:"점심·저녁형 (11~21시)",slots:[2,3,4]},pm:{nm:"저녁·심야형 (17~새벽)",slots:[4,5,0]}};
const STAFF=[.80,1.00,1.12];
const MINWAGE={2021:8720,2022:9160,2023:9620,2024:9860,2025:10030};
const ACT={
 keep:{nm:"그대로 버티기",d:"아무것도 바꾸지 않아요"},
 price:{nm:"가격 10% 내리기",d:"손님 +12%·단골이 빨리 붙지만 하나 팔아 남는 돈이 줄어요"},
 menu:{nm:"메뉴 늘리기",d:"매출 +6%, 원가 4% 오름"},
 deliv:{nm:"배달 시작",d:"매출 +18%, 그 매출의 25%는 수수료"},
 hire:{nm:"직원 한 명 더",d:"더 많이 받지만 인건비가 붙어요"},
 cut:{nm:"직원 한 명 줄이기",d:"인건비는 줄고 매출도 조금 줄어요"},
 close:{nm:"가게 접기",d:"보증금 들고 나가요 · 이것도 전략"}};
const GU={"11110":"종로구","11140":"중구","11170":"용산구","11200":"성동구","11215":"광진구","11230":"동대문구","11260":"중랑구","11290":"성북구","11305":"강북구","11320":"도봉구","11350":"노원구","11380":"은평구","11410":"서대문구","11440":"마포구","11470":"양천구","11500":"강서구","11530":"구로구","11545":"금천구","11560":"영등포구","11590":"동작구","11620":"관악구","11650":"서초구","11680":"강남구","11710":"송파구","11740":"강동구"};
const MIN_N=30;
/* 결정 시점(분기 번호): 첫해 7월, 그다음 해마다 1월 */
const DQ=[2,4,8,12,16];
const LIVING=250; /* 사장 생활비 월 250만(가정) */

/* 동 하나의 기준선 — 30집 미만이면 구 합계로 */
function baseline(data,code){
 const r=data.d[code]; if(!r) return null;
 let src=r,gu=false;
 const avgN=r.n.reduce((a,b)=>a+b,0)/r.n.length;
 if(avgN<MIN_N){
  const p=code.slice(0,5),agg={s:r.s.map(()=>0),n:r.n.map(()=>0),o:r.o.map(()=>0),c:r.c.map(()=>0),t:[0,0,0,0,0,0]};
  for(const k in data.d){if(k.slice(0,5)!==p)continue;const x=data.d[k];
   for(let i=0;i<x.s.length;i++){agg.s[i]+=x.s[i];agg.n[i]+=x.n[i];agg.o[i]+=x.o[i];agg.c[i]+=x.c[i];}
   x.t.forEach((v,i)=>agg.t[i]+=v*(x.s.reduce((a,b)=>a+b,0)));}
  const tt=agg.t.reduce((a,b)=>a+b,0)||1;agg.t=agg.t.map(v=>Math.round(v/tt*100));
  src=agg;gu=true;
 }
 const per=src.s.map((s,i)=>src.n[i]>0?s/src.n[i]:0);
 for(let i=0;i<per.length;i++) if(!per[i]) per[i]=per[i-1]||per.find(v=>v)||0;
 const nAvg=Math.round(src.n.reduce((a,b)=>a+b,0)/src.n.length);
 return {per,n:src.n,o:src.o,c:src.c,t:src.t,gu,nAvg,gnm:GU[code.slice(0,5)]||""};
}
function hoursFactor(t,h){const sh=HOURS[h].slots.reduce((a,i)=>a+t[i],0)/100;return Math.max(.45,Math.min(1.25,sh/.72));}
/* 실제 폐업률: 연 폐업 점포 ÷ 평균 점포 */
function realCloseRate(b){let c=0,n=0;for(let i=0;i<b.c.length;i++){c+=b.c[i];n+=b.n[i];}return n?c/(n/4):0;}

/* 한 판: setup {ind,loc,hours,staff,fund}, acts[DQ 시점마다 선택 5개] */
function play(b,setup,acts){
 const I=IND[setup.ind],L=LOC[setup.loc],hf=hoursFactor(b.t,setup.hours);
 const base0=b.per.slice(0,4).reduce((a,v)=>a+v,0)/4;
 const rent0=Math.round(base0*L.rent);
 const deposit=rent0*6, own=5000;
 const need=I.ent+deposit, loan=Math.max(0,need+3000-own)+(setup.fund===10000?3000:0);
 let cash=own+loan-need, staff=setup.staff, ramp=.70, rent=rent0;
 const st={price:false,menu:false,deliv:false};
 const months=[],years=[]; let neg=0,closedAt=null,quit=false,yi=0;
 for(let q=0;q<b.per.length;q++){
  const y=2021+Math.floor(q/4);
  if(q%4===0&&q>0)rent=Math.round(rent*1.04);
  if(DQ.includes(q)){
   const a=acts[yi++]||"keep";
   if(a==="close"){quit=true;closedAt=q*3;break;}
   if(a==="price")st.price=true; if(a==="menu")st.menu=true; if(a==="deliv")st.deliv=true;
   if(a==="hire")staff=Math.min(2,staff+1); if(a==="cut")staff=Math.max(0,staff-1);
  }
  if(q%4===0)years.push({y,cash0:cash,staff});
  for(let m=0;m<3;m++){
   ramp=Math.min(1.10,ramp+(st.price?.035:.02));
   let sales=b.per[q]*ramp*L.sales*hf*STAFF[staff];
   if(st.menu)sales*=1.06; if(st.price)sales*=1.008;
   const dsales=st.deliv?sales*.18:0; sales+=dsales;
   let mat=I.mat*(st.menu?1.04:1)/(st.price?.9:1);
   const wage=Math.round(staff*MINWAGE[y]*209/1e4);
   const cost=sales*mat+rent+wage+sales*.05+50+dsales*.25+loan*.05/12+LIVING;
   const profit=sales-cost; cash+=profit;
   months.push({q,sales:Math.round(sales),cost:Math.round(cost),profit:Math.round(profit),cash:Math.round(cash)});
   if(cash<0){if(++neg>=3){closedAt=q*3+m+1;break;}}else neg=0;
  }
  if(closedAt!==null)break;
 }
 const end=Math.round(cash+deposit-loan);
 const bankrupt=closedAt!==null&&!quit;
 return {months,years,end,gain:end-own,bankrupt,quit,lived:closedAt===null?60:closedAt,rent0,deposit,hf,base0,loan,need};
}
const api={DQ,LIVING,IND,LOC,HOURS,ACT,GU,MINWAGE,baseline,play,hoursFactor,realCloseRate,MIN_N};
if(typeof module!=="undefined")module.exports=api; else root.ENG=api;
})(this);
