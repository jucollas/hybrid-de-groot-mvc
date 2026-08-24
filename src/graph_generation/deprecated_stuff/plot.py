import numpy as np
import openpyxl # para excel


def create_clean_xlsx( filename:str, sheetname:str ) :
	"""
	Se asegura que existe un archivo .xlsx con nombre 'filename' y que existe un sheet de este
		con nombre 'sheetname' que esta vacia
	"""
	try:
		workbook = openpyxl.load_workbook( filename );
	except:
		workbook = openpyxl.Workbook();

	# La vacia si ya esta, esto para evitar que celdas de anteriores ejecuciones queden con datos
	if ( sheetname in workbook.sheetnames ): workbook.remove( workbook[sheetname] );
	workbook.create_sheet(sheetname) # la crea
	workbook.save( filename ); # guarda el workbook


def writeTable( filename:str, dat:list[list[int]], strt:tuple[int,int],sheetname:str="_",tablename:str="",col=[],row=[] ) -> None:
	"""
	Escribe la tabla 'tablename' con los datos en 'dat', en la sheet 'sheetname' y el archivo 'filename'.
		Todo esto lo comienza desde (strt[0],strt[1]) siendo la esquina superior derecha de la tabla
	"""
	workbook = openpyxl.load_workbook( filename );
	worksheet = workbook[sheetname]
	worksheet[openpyxl.utils.get_column_letter(strt[0])+str(strt[1])] = tablename;
	if ( col!=[] and row!=[] ):
		for i in range(1,len(dat)+1):
			worksheet[openpyxl.utils.get_column_letter( strt[0] )+str(strt[1]+i+1)] = "[%d]"%(row[i-1])
		for j in range(1,len(dat[0])+1):
			worksheet[openpyxl.utils.get_column_letter( strt[0]+j )+str(strt[1]+1)] = "[%d]"%(col[j-1])
		strt=(strt[0]+1,strt[1]+1);
	
	for i in range(len(dat)):
		for j in range(len(dat[i])):
			worksheet[openpyxl.utils.get_column_letter( strt[0]+j )+str(strt[1]+i+1)] = dat[i][j] if dat[i][j] != float("inf") else "INF";
	workbook.save( filename );

import sys

def read_data():
	Elem=6

	it_am,girth,outdeg,eps,sz_indeg,n_sz_sz,seed=sys.stdin.readline().strip().split()
	it_am=int(it_am); sz_indeg=int(sz_indeg); n_sz_sz=int(n_sz_sz);
	indeg=list(map(int,sys.stdin.readline().strip().split()))
	n_sz =list(map(int,sys.stdin.readline().strip().split()))

	diam=[]
	dg=[]
	s5=[]
	wf=[]## [indeg]
	for i in range(sz_indeg):
		diam.append([])
		dg.append([])
		s5.append([])
		wf.append([])## [indeg][n_sz]
		for j in range(n_sz_sz):
			sys.stdin.readline().strip()# empty line
			diam[-1].append(list(map(int,sys.stdin.readline().strip().split())))
			al_mod=[dg,s5,wf]
			for md in al_mod:
				md[-1].append([])### [indeg][n_sz][data]
				Type_in_4k=[int,int,int,float,float,float]
				assert(len(Type_in_4k)==Elem)
				for k in range(Elem):### [indeg][n_sz][data][ind]
					md[-1][-1].append(list(map(Type_in_4k[k],sys.stdin.readline().strip().split())))
					assert(len(md[-1][-1][-1])==it_am)
	return diam,dg,s5,wf,indeg,n_sz,it_am

import matplotlib.pyplot as plt
def gen_scatterplot(raw_data,x_axis:list[int], legend:list[str],ylabel:str, filename:str)->None:
	data=[]
	#print("xdxdxdxd")
	for batch in raw_data:
		#print(len(batch),len(x_axis))
		#print(x_axis)
		assert(len(batch)==len(x_axis))
		data.append([])
		for i in range(len(x_axis)):
			for y_val in batch[i]:
				data[-1].append((x_axis[i],y_val))
	assert(len(legend)==len(data))
	plt.xscale('log')#### xdxdxdxd
	for i in range(len(legend)):
		x=[el[0] for el in data[i]]
		y=[el[1] for el in data[i]]
		plt.scatter(x,y,label=str(legend[i]))
	plt.legend()
	plt.xlabel("In_degree (logarithmic)")
	plt.ylabel(ylabel)
	if(filename==""):
		plt.show()
	else:
		plt.savefig(filename,dpi=300)
def saving_the_universe____scatterversion():
	Elem=5
	Model=3

	diam,sg,s5,wf,indeg,n_sz,_=read_data()
	for i in range(len(indeg)):
		up_filename=""
		#up_filename="_"+str(indeg[i])+".png"
		in_prf= lambda prf:prf+up_filename if up_filename!=""else ""
		gen_scatterplot([diam[i]],n_sz,[""],"Diameter",in_prf("diam"))
		st,cm,rt,mm,dl=[[[]for _ in range(Model)]for _ in range(Elem)]
		for j in range(len(n_sz)):
			al_mod=[sg,s5,wf]
			for k in range(Model):
				st[k].append(al_mod[k][i][j][0])
				#print(st[k][-1],"ggs hermano")
				cm[k].append(al_mod[k][i][j][1])
				rt[k].append(al_mod[k][i][j][2])
				mm[k].append(al_mod[k][i][j][3])
				dl[k].append(al_mod[k][i][j][4])
		m_name=["DeGroot","S5","Wafle"]
		gen_scatterplot(st,n_sz,m_name,"Time(Steps)",in_prf("step"))
		gen_scatterplot(cm,n_sz,m_name,"Communications",in_prf("comm"))
		gen_scatterplot(rt,n_sz,m_name,"Runtime(miliseconds)",in_prf("runTime"))
		gen_scatterplot(mm,n_sz,m_name,"Max-Min",in_prf("MaxMin"))
		gen_scatterplot(dl,n_sz,m_name,"Max-Min change",in_prf("maxMinChange"))
def gen_boxplot(data,x_axis:list[int], legend:list[str],ylabel:str,title:str, filename:str)->None:
	
	
	fig, ax = plt.subplots()
	ax.set_title(title)
	ax.set_ylabel(ylabel)
	ax.boxplot(data,tick_labels=legend,showfliers=False)
	if(filename==""):
		plt.show()
	else:
		plt.savefig(filename,dpi=300)
	plt.close()

def saving_the_universe(outlier=False,filename="promedios.xlsx",ext=""):
	Elem=6
	Model=3

	diam,sg,s5,wf,indeg,n_sz,it_am=read_data()
	p_diam=[[0 for _ in range(len(n_sz)) ]for _ in range(len(indeg))]
	steps,comm,runtime,max_min,mm_delta,copi=[[[[0 for _ in range(len(n_sz))]for _ in range(len(indeg))] for _ in range(Model)]for _ in range(Elem)]
	cnt_steps,cnt_comm,cnt_runtime,cnt_max_min,cnt_mm_delta,cnt_copi=[[[[0 for _ in range(len(n_sz))]for _ in range(len(indeg))] for _ in range(Model)]for _ in range(Elem)]
	for i in range(len(indeg)):
		for j in range(len(n_sz)):
			up_filename=""
			up_filename="_"+str(indeg[i])+"_"+str(n_sz[j])+".png"
			title="In degree <"+str(indeg[i])+"> _ vertices <"+str(n_sz[j])+">"
			in_prf= lambda prf:prf+up_filename if up_filename!=""else ""
			##gen_boxplot([diam[i]],n_sz,[""],"Diameter",ext+in_prf("diam"))
			p_diam[i][j]=sum(diam[i][j])/it_am
			st,cm,rt=[[]for _ in range(3)]
			al_mod=[sg,s5,wf]

			
			for k in range(Model):
				st.append(al_mod[k][i][j][0])
				#print(st[k][-1],"ggs hermano")
				cm.append(al_mod[k][i][j][1])
				rt.append(al_mod[k][i][j][2])
				def take_out_outlier(lst:list)->list:
					lst=np.array(lst)
					q1,q3=np.percentile(lst,[25,75])
					iqr=(q3-q1)*1.5
					return list(lst[(lst>=q1-iqr)&(lst<=q3+iqr)])
				def calc_prom(lst:list,obj,cnt)->list:
					lst=take_out_outlier(lst) if outlier else lst
					assert(len(lst)>0),"Que putas?????"
					cnt[k][i][j]=len(lst)
					obj[k][i][j]=sum(lst)/len(lst)
				calc_prom(al_mod[k][i][j][0],steps   ,cnt_steps   )
				calc_prom(al_mod[k][i][j][1],comm    ,cnt_comm    )
				calc_prom(al_mod[k][i][j][2],runtime ,cnt_runtime )
				calc_prom(al_mod[k][i][j][3],max_min ,cnt_max_min )
				calc_prom(al_mod[k][i][j][4],mm_delta,cnt_mm_delta)
				calc_prom(al_mod[k][i][j][5],copi    ,cnt_copi    )
			m_name=["DeGroot","S5","Wafle"]
			gen_boxplot(st,n_sz,m_name,"Time(Steps)",title,ext+in_prf("step"))
			gen_boxplot(cm,n_sz,m_name,"Communications",title,ext+in_prf("comm"))
			gen_boxplot(rt,n_sz,m_name,"Runtime(miliseconds)",title,ext+in_prf("runTime"))
	sheets=["steps","comm","runt","maxMin","maxMin_delta","final_opinion"]
	al_sht=[steps,comm,runtime,max_min,mm_delta,copi]
	al_cnt_sht=[cnt_steps,cnt_comm,cnt_runtime,cnt_max_min,cnt_mm_delta,cnt_copi]
	create_clean_xlsx(ext+filename,"diameter")
	writeTable(ext+filename,p_diam,(1,1),"diameter","_",n_sz,indeg)
	for i in range(len(sheets)):
		create_clean_xlsx(ext+filename,sheets[i])
		m_name=["DeGroot","S5","Wafle"]
		strt=(1,1)
		for j in range(len(m_name)):
			writeTable(ext+filename,al_sht[i][j],strt,sheets[i],m_name[j],n_sz,indeg)
			writeTable(ext+filename,al_cnt_sht[i][j],(3+len(n_sz),strt[1]),sheets[i],m_name[j]+"_cnt(elements used,perhaps no outliers)",n_sz,indeg)
			strt=(1,strt[1]+len(indeg)+3)



if __name__ == '__main__':
	saving_the_universe(outlier=True,ext="./uniform/")
	#saving_the_universe(outlier=True,ext="./louvain/")


			





