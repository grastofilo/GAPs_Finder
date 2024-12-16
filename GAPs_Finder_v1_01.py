#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 11:34:33 2024

@author: ninni
"""

import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
#import matplotlib.dates as mdates
from pprint import pprint

from plotly.subplots import make_subplots
import plotly.graph_objects as go

#import ipywidgets as widgets
from IPython.display import display, clear_output

import yfinance as yf
from finvizfinance.quote import finvizfinance


import streamlit as st

#from st_aggrid import AgGrid






#%%


# QUESTO BLOCCO CARICA I DATI DA YAHOO FINANCE E POI ELABORA IL DF DATI_STORICI
# QUINDI COME PRIMA COSA LANCIO LA FUNZIONE CHE FARà L'ELABORAZIONE PER POI CARICARE I DATI DA YFINANCE
# E LANCIARE LA FUNZIONE elaborazione()


#%%



# QUI ELABORO il df dati_storici e CREO  le features 'Max % UP' - 'Max % DOWN' - 'Open to Close %' e 'chiusura'


def elaborazione(dati_storici):
    
    #global dati_storici_ADJ 
    
   
    
    
    # creo un df transitorio dove inserire i risultati del calolo dello split factor:

    trans = pd.DataFrame(index=range(0,len(dati_storici)))
    trans['split_factor'] = 0



    # inizio con il calcolo:

    split_factor = 1


    for a in range((len(dati_storici)-1),-1,-1):
            if dati_storici['Stock Splits'].iloc[a] > 0:
                    #print(a)
                    
                    #aaa = split_factor
                    trans.loc[a,'split_factor'] = split_factor
                    split_factor = split_factor*dati_storici['Stock Splits'].iloc[a]
                    #print(split_factor)                                                              
                    #trans.loc[a,'split_factor'] = aaa
                          
            else:
                
                    trans.loc[a,'split_factor']=split_factor

                                
                            
    
    
    
    
    dati_storici['Gap %'] = ((dati_storici['Open']*100)/dati_storici['Close'].shift(1))-100

    colonna_da_spostare = dati_storici.pop('Gap %')
    dati_storici.insert(1,'Gap %',colonna_da_spostare)
    
    dati_storici['Max % UP'] = ((dati_storici['High']*100)/(dati_storici['Open']))-100
    dati_storici['Max % DOWN'] = ((dati_storici['Low']*100)/(dati_storici['Open']))-100
    dati_storici['Open to Close %'] = ((dati_storici['Close']*100)/(dati_storici['Open']))-100
    dati_storici['Chiusura'] = dati_storici.apply(lambda x: 'RED' if x['Open to Close %']<0 \
                                                  else 'GREEN' if x['Open to Close %']>0 else '=open', axis=1)
    
    dati_storici = dati_storici.round(3)
    
    
    # creo una copia di dati_storici per mantenere inalterati i prezzi corretti che serviranno x il grafico
    dati_storici_ADJ = dati_storici.copy()
    
    
    return trans,dati_storici_ADJ




#%%

# CREO UN PICCOLO DF CON I STOCK_SPLIT/REVERSE_STOCK_SPLIT

def stock_split(dati_storici):
    
    #global dati_storici
    
    # creo la tabella con gli stock split factors
    split_df = dati_storici[(dati_storici['Stock Splits']>0)].loc[:,['Date','Stock Splits']] 
    split_df.reset_index(drop=True,inplace=True)
    split_df.index = split_df.index +1

    split_df['Stock Splits'] = split_df['Stock Splits'].apply(lambda x: f'1/{int(1/x)}' \
                               if x<1 else f'{x:.1f}/1'.replace('.',','))
    
    
    split_df.rename(columns={'Stock Splits':'Splits / REV Splits'},inplace=True)
    
    
    return split_df
    
    #st.write(split_df) 
    
    

 # # creo la tabella con gli stock split factors
 # split_df = dati_storici[(dati_storici['Stock Splits']>0)].loc[:,['Date','Stock Splits']] 
 # split_df['Stock Splits'] = split_df['Stock Splits'].apply(lambda x: f'1/{int(1/x)}' \
 #                            if x<1 else f'{x:.1f}/1'.replace('.',','))

 # split_df.rename(columns={'Stock Splits':'values'},inplace=True)
 # split_df.rename(columns={'Date':'nomi'},inplace=True)
 


#%%


# CARICO I DATI FONDAMENTALI DA FINVITZ

def finvitz_func(nome_ticker):
    
    
    
   
    
    tentativi = 1
    while tentativi < 5:

        try:
            
            # fondamentali da finviz
            
            finvitz_stampa = st.empty()
            
            
            with finvitz_stampa.container():
                
                st.write('loading...')
                
                
                stock = finvizfinance(nome_ticker)
                finvitz_data = stock.ticker_fundament()
                    
                
                fondamentali = {'sector':finvitz_data.get("Sector"),
                                'industry':finvitz_data.get("Industry"),
                                'market cap': finvitz_data.get('Market Cap'),           
                                'shares float': finvitz_data.get('Shs Float'),
                                'insider Own.':finvitz_data.get('Insider Own'),
                                'inst. Own.': finvitz_data.get('Inst Own'),
                                'Short Float':finvitz_data.get('Short Float')
                                                                                        }
                    
                finvitz_stampa.empty()
                return fondamentali
                break   
                
                

        
        except: #Exception as e:
            
            #print(f'tentativo {tentativi}/5 di accesso ai dati finvitz fallito')
            finvitz_stampa.empty()
            tentativi += 1
            #display(e)
        
        
    if tentativi == 5: 
        print("caricamento dati fondamentali da FINVITZ fallito")
        fondamentali = {'sector':' - ',
                        'industry':' - ',
                        'market cap':' - ',           
                        'shares float':' - ',
                        'insider Own.':' - ',
                        'inst. Own.':' - ',
                        'Short Float':' - ' }
        return fondamentali 





#%%


# CARICO I VALORI di PREZZO DA YAHOO FINANCE


def yfinance_func(nome_ticker):
    
    
    ticker = yf.Ticker(nome_ticker.upper())
    dati_storici = ticker.history(period="max")  # dati periodo massimo disponibile
    
    
    
    #if  not dati_storici.empty:
    if len(dati_storici.columns)==7:   
        
        # APPORTO dei CORRETTIVI al DF dati_storici  ORIGINALE
        dati_storici = dati_storici.reset_index()
        dati_storici['Data'] = dati_storici['Date'].dt.date
        dati_storici.drop('Date',inplace=True,axis=1)
        dati_storici.rename(columns={'Data':'Date'},inplace=True)
        colonna_da_spostare = dati_storici.pop('Date')
        dati_storici.insert(0,'Date',colonna_da_spostare)
        
        
        
        return dati_storici
        # converto in formato datetime
        #dati_storici['Date'] = pd.to_datetime(dati_storici['Date'])
        
        
        
    else:
        if dati_storici.empty:
            st.write('Nonexistent or delisted title')
            return dati_storici
        
        if len(dati_storici.columns)==8:
            st.write(f"{nome_ticker.upper()} it's not a stock")
            dati_storici = pd.DataFrame()
            return dati_storici
            
        

#%%




                

# LA FUNZIONE CHE SEGUE CERCA I GAPS ALL'INTERNO DEL DF dati_storici 
# e CREA UN NUOVO DF GAPS CHE LI CONTIENE, 
# VEDIAMO IL RISULTATO ATTRAVERSO IL DF visual_gaps CHE E' UNA COPIA OTTIMIZZATA PER LA VISIONE 




def ricerca_gaps(nome_ticker,dati_storici,trans,gap_perc_A,gap_perc_B,volume,prezzo_A,prezzo_B):
    

    # print(nome_ticker.upper(),'\n')
    # print(f'Storico GAPs >= {gap_perc_A}%')
    # print(f'con Volume minimo >= {volume/1000000:.2f} mln \n')
    
    global gaps
    
    gaps = dati_storici.iloc[:,[0,1,2,3,4,5,9,10,11,-1,6]].copy()
    
    
    # rettifico al valore originale i dati di ogni riga del df gaps:
    
    if gaps.shape[0]>0:
        
        # gaps['Open'] = gaps.apply(lambda x: x['Open']*trans.loc[x.name,'split_factor'],axis=1)
        # gaps['High'] = gaps.apply(lambda x: x['High']*trans.loc[x.name,'split_factor'],axis=1)
        # gaps['Low'] = gaps.apply(lambda x: x['Low']*trans.loc[x.name,'split_factor'],axis=1)
        # gaps['Close'] = gaps.apply(lambda x: x['Close']*trans.loc[x.name,'split_factor'],axis=1)
        # gaps['Volume'] = gaps.apply(lambda x: x['Volume']/trans.loc[x.name,'split_factor'],axis=1)
        
        gaps['Open'] = gaps.apply(lambda x: x['Open']*trans.loc[x.name,'split_factor'] if\
                                  (trans.loc[x.name,'split_factor']< 1) else \
                                      (x['Open']/trans.loc[x.name,'split_factor']),axis=1)
            
        gaps['High'] = gaps.apply(lambda x: x['High']*trans.loc[x.name,'split_factor'] if\
                                  (trans.loc[x.name,'split_factor']< 1) else \
                                      (x['High']/trans.loc[x.name,'split_factor']),axis=1)
            
        gaps['Low'] = gaps.apply(lambda x: x['Low']*trans.loc[x.name,'split_factor'] if\
                                  (trans.loc[x.name,'split_factor']< 1) else \
                                      (x['Low']/trans.loc[x.name,'split_factor']),axis=1)
            
        gaps['Close'] = gaps.apply(lambda x: x['Close']*trans.loc[x.name,'split_factor'] if\
                                  (trans.loc[x.name,'split_factor']< 1) else \
                                      (x['Close']/trans.loc[x.name,'split_factor']),axis=1) 
            
            
        gaps['Volume'] = gaps.apply(lambda x: x['Volume']/trans.loc[x.name,'split_factor'] if\
                                  (trans.loc[x.name,'split_factor']< 1) else \
                                      (x['Volume']*trans.loc[x.name,'split_factor']),axis=1)     
            
        
            
            
        
        
        
        
        gaps = gaps[(gaps['Gap %']>=gap_perc_A)&\
                        (gaps['Gap %']<=gap_perc_B)&\
                        (gaps['Volume']>=volume)&(gaps['Open']>=prezzo_A)&(gaps['Open']<=prezzo_B)]
    
    
        
        # Effettuo adesso una copia del df gaps - solamente per poterla visualizzare
    
        display_gaps = gaps.copy()
        
        
        display_gaps['Volume'] = display_gaps.apply(lambda x: f"{x['Volume']:,.0f}".replace(',','.'),axis=1)
        
        display_gaps = display_gaps.round(2)
        
        
        display_gaps[['Gap %', 'Open', 'High', 'Low', 'Close', 'Max % UP',
           'Max % DOWN', 'Open to Close %']]=\
        display_gaps[['Gap %', 'Open', 'High', 'Low', 'Close', 'Max % UP',
           'Max % DOWN', 'Open to Close %']].astype(str).apply(lambda x: x.str.replace('.',',',regex=False))
        
        
        
        display_gaps.reset_index(drop=True,inplace=True)
        display_gaps.index = display_gaps.index+1
    
        #st.dataframe(display_gaps, use_container_width=True)
        #st.dataframe(display_gaps)
        #AgGrid(display_gaps, height=300, fit_columns_on_grid_load=True)
       
        
        
    
        return(display_gaps)
        
        
        
    else: 
        print(f' il titolo {nome_ticker.value} non ha nessun gap superiore o uguale al {gap_perc_A}%')
        
        
        
#%%

## VISUALIZZA IL GRAFICO DEL GAP

def visual_gap(nome_ticker,n_gap,dati_storici_ADJ):
    
    global gaps
    #global dati_storici_ADJ
    
    finestra_daily = 100

    elementi_da_inizio_df = gaps.index[n_gap]
    if elementi_da_inizio_df > round(finestra_daily/2):
        finestra_A = round(finestra_daily/2)
    else:
        finestra_A = elementi_da_inizio_df
        
    #print(finestra_A )
    
        
    elementi_da_fine_df = (dati_storici_ADJ.shape[0])-elementi_da_inizio_df
    if elementi_da_fine_df > round(finestra_daily/2):
        finestra_B = round(finestra_daily/2)
    else:
        finestra_B = elementi_da_fine_df
    #print(finestra_B )    
    
    
    
    
    
    df = dati_storici_ADJ.iloc[gaps.index[n_gap]-(finestra_A)\
                               :gaps.index[n_gap]+(finestra_B),:].copy()
    
    
    # Crea una colonna con il testo da mostrare nel tooltip
    df['hover_text'] = (
        "Data: " + df['Date'].astype(str) + "<br>" +
        "Open: " + df['Open'].astype(str) + "<br>" +
        "High: " + df['High'].astype(str) + "<br>" +
        "Low: " + df['Low'].astype(str) + "<br>" +
        "Close: " + df['Close'].astype(str) + "<br>" +
        "Gap %: " + df['Gap %'].astype(str) + "<br>"
    )
    
    df['volume_text'] = df.apply(lambda x: f"{x['Volume']:,.0f}".replace(",","."),axis=1)
    df['volume_text'] = ("Volume: "+df['volume_text'].astype(str))
    
    
    
    # Crea il grafico con il testo personalizzato
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.8, 0.2],
        vertical_spacing= 0.15
    )
    
    # Aggiunta delle candele
    fig.add_trace(
        go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="Daily",
            hovertext=df['hover_text'],  # Assegna il testo personalizzato
            hoverinfo="text"  # Specifica di mostrare solo il testo personalizzato
        ),
        row=1, col=1
    )
    
    # Aggiunta del volume
    fig.add_trace(
        go.Bar(
            x=df['Date'],
            y=df['Volume'],
            name="Volume",
            hovertext=df['volume_text'],
            hoverinfo="text",
            marker_color='blue',
            opacity=0.6
        ),
        row=2, col=1
    )
    
    
    
    if finestra_A >= 5:
        finestra_visione_A = 5 
    else:
        finestra_visione_A = finestra_A-1   
    
    if finestra_B >= 5:
        finestra_visione_B = 5 
    else:
        finestra_visione_B = finestra_B-1
    
    
    
    
    # Layout
    fig.update_layout(
    title=f"          {nome_ticker.upper()} -  Grafico Gap del {gaps.iloc[n_gap, 0]}",
    yaxis_title="Prezzo",
    xaxis_rangeslider={'thickness': 0.08, 'visible': True},
    template="plotly_white",
    width=800,
    height=600,
    shapes=[
        {
            'type': "rect",
            'xref': "x",
            'yref': "paper",
            'x0': df['Date'].loc[gaps.index[n_gap]],
            'x1': df['Date'].loc[gaps.index[n_gap] - 1],
            'y0': 0.80,
            'y1': 0.40,
            'fillcolor': 'Orange',
            'opacity': 0.1,
            'layer': "below",
            'line_width': 0
        }
    ]
)
    

    fig.update_xaxes(
    range=[
        df['Date'].loc[gaps.index[n_gap] - finestra_visione_A], 
        df['Date'].loc[gaps.index[n_gap] + finestra_visione_B]
    ]
)
    

    
    
    ## Riposiziona lo slider manualmente per metterlo sotto i volumi
    #fig.update_layout(
    #    xaxis_rangeslider=dict(
    #        visible=True,
    #        yanchor="bottom",  # Posiziona lo slider sotto
    #        thickness=0.1      # Spessore dello slider
    #    ),
    #    height=700  # Aumenta l'altezza per fare spazio allo slider
    #)
    
    
    # Configura il grafico per migliorare l'interattività
    st.plotly_chart(fig, use_container_width=False, config={
        'displayModeBar': True,  # Mostra la barra degli strumenti
        'responsive': True,      # Adatta il grafico al contenitore
        'scrollZoom': True,      # Abilita lo zoom con scroll
        'staticPlot': False     # Permette interazioni
    })




        


        
#%%    
        
#  INTERFACCIA UTENTE:
    
    
# QUI SETTO COME UTILIZZARE LO SPAZIO DELLA PAGINA WEB



st.set_page_config(
    page_title="GAPs Finder",
    page_icon="📈",
    layout="wide",  # 'centered' o 'wide'
    initial_sidebar_state="expanded",  # 'expanded' o 'collapsed'
                 ) 


# st.markdown(
#     """
#     <style>
#     html {
#         zoom: 0.9; /* Riduce tutto al 90% */
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )




#dati_storici = None



col1,col2,col3 = st.columns([0.1,0.46,0.44])   
    
    
    

# INSERISCO il TICKER
global nome_ticker






with col1:
    
    
    
    st.markdown("""
            <style>
                .stTextInput>div>div>input {
                    font-size: 13px !important;  /* Riduce la dimensione del font */
                }
                
                /* Modifica il campo di input del testo */
                
                .stTextInput input {
                    font-size: 12px !important;  /* Riduce la dimensione del testo nell'input */
                    }  
            </style>
        """, unsafe_allow_html=True)

      
      
    
    with st.form(key=f'GAPs_Finder'):
         nome_ticker = st.text_input('**GAPs Finder v1.01**',placeholder='Enter the Ticker').strip()
         bottone_ricerca = st.form_submit_button('ricerca GAPs')
         
    
    stampa_col1 = st.empty()  
        
    
    
    if bottone_ricerca:
        
        
        #stampa_col1.empty()
        st.session_state.clear()
        
        st.session_state['slider_gaps']=(30,1000)
        st.session_state['slider_volume']=1
        st.session_state['slider_price']=(2,200)
        
            
        
        
        
        if nome_ticker:
            
            
            dati_yfinance = yfinance_func(nome_ticker)
            
            
            if not dati_yfinance.empty:
             
                trans,dati_storici_ADJ = elaborazione(dati_yfinance)
                dati_split = stock_split(dati_yfinance)
                fondamentali_finvitz = finvitz_func(nome_ticker)
                

                st.session_state['dati_storici'] = dati_yfinance
                st.session_state['trans'] = trans
                st.session_state['fondamentali_finvitz'] = fondamentali_finvitz
                st.session_state['dati_split'] = dati_split
                st.session_state['dati_storici_ADJ'] = dati_storici_ADJ
                
            #else: 
             #   st.write('non trovo dati su questo titolo')
                
        else:
            st.warning('Enter the Ticker')
            
            
            
            
            
            
    if 'dati_storici' in st.session_state and st.session_state['dati_storici'] is not None:
        
        
        with stampa_col1.container():
            
            
            st.write("")
            st.write("")
            
            st.markdown(f"""
                    <div style="font-size: 22px; font-weight: bold;">{nome_ticker.upper()}</div>
                    <div style="font-size: 14px;">{st.session_state['fondamentali_finvitz']['sector']}</div>
                    <div style="font-size: 14px;">{st.session_state['fondamentali_finvitz']['industry']}</div>
                    <br> <!-- Rigo vuoto aggiunto qui -->
                    <div style="font-size: 14px;">  
                    <b>market cap</b>: {st.session_state['fondamentali_finvitz']['market cap']}<br>
                    <b>shares float</b>: {st.session_state['fondamentali_finvitz']['shares float']}<br>
                    <b>insider Own</b>: {st.session_state['fondamentali_finvitz']['insider Own.']}<br>
                    <b>inst. Own</b>: {st.session_state['fondamentali_finvitz']['inst. Own.']}<br>
                    <b>Short Float</b>: {st.session_state['fondamentali_finvitz']['Short Float']}
                    </div>
                    """, unsafe_allow_html=True)

               
               
            
            if not st.session_state['dati_split'].empty:
                st.write("")
                st.write("")
                st.markdown("<div style='font-size: 14px;'> <b>Splits / Reverse Splits</b> </div>", unsafe_allow_html=True)
                st.write("")

                for a,b in  st.session_state['dati_split'].iterrows():
                    #st.write(f"{b['Date']} - {b['Splits / REV Splits']}")
                    st.markdown(f"""
                            <div style="font-size: 13px;">
                                {b['Date']} <b>&nbsp;&nbsp;--&nbsp;&nbsp;</b> {b['Splits / REV Splits']}
                            </div>
                        """, unsafe_allow_html=True)


                    
               
                
               
                
with col2:
    
    st.markdown(
            """
            <style>
            table {
                font-size: 12px;  /* Dimensione del carattere */
                width: 100%;  /* Larghezza della tabella */
                margin-left: auto;  /* Allinea al centro */
                margin-right: auto; /* Allinea al centro */
            }
            thead th {
                font-size: 14px;  /* Dimensione del carattere dell'intestazione della tabella  */
            }
            tbody td {
                font-size: 13px;  /* Dimensione del carattere del contenuto della tabella */
            }
            
            
            
            
            .stTable td, .stTable th {
                white-space: nowrap !important;  /* Impedisce il ritorno a capo */   
            }
            
            # .stTable {
            #     font-size: 16px;  /* Imposta la dimensione del font */
            #     table-layout: fixed;  /* Fissa la larghezza delle colonne */
            #     width: 100%;
            #}
            
            
            .stSlider {
                margin-bottom: -20px; /* Riduce lo spazio verticale tra gli slider */
            }

            
  
            .stSlider div[data-testid="stMarkdownContainer"] p {
                font-size: 13px !important; /* Riduce l'etichetta dello slider */
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    
   
    
     
    if 'dati_storici' in st.session_state and st.session_state['dati_storici'] is not None:
        
        

            # Slider per gestire i parametri di ricerca
            
            
           col2_1,col2_2,col2_3 = st.columns([0.25,0.5,0.25])
           with col2_2:
               gap_A,gap_B = st.slider("**Gap %**",0,1000,step=5,key='slider_gaps')
                    
               volume = st.slider("**Volume Minimo Mln**", 0,500,step=1,key='slider_volume')
                    
               prezzo_A,prezzo_B = st.slider('**prezzo minimo $**',0,200,step=1,key='slider_price')
               
               
               
              
           v_gaps = ricerca_gaps(nome_ticker,st.session_state['dati_storici'],\
                                     st.session_state['trans'],gap_A,gap_B,volume*1_000_000,prezzo_A,prezzo_B) 


           
           st.write("");st.write("")
           
           
               
           if not v_gaps.empty:
               st.table(v_gaps)
           else:
               st.markdown(
                f"""
                <div style="text-align: center; font-size: 15px;">
                    <b>{nome_ticker.upper()}</b> non ha giornate rispondenti ai parametri settati
                </div>
                """,
                unsafe_allow_html=True)

            
            
           
            
           
           if not v_gaps.empty:
                
                with col3:
                    
                    col3_1,col3_2 = st.columns([0.18,0.82])
                    with col3_1:
                        
                        options = list(v_gaps.index)
                        n_gap = st.selectbox('**gap da visualizzare**',options)
                        
                    if st.button('visualizza'):
                        try:
                            visual_gap(nome_ticker,(n_gap-1),st.session_state['dati_storici_ADJ'])
                        except:
                            st.markdown(
                             f"""
                             <div style="text-align: center; font-size: 15px;">
                                 grafico non disponibile
                             </div>
                             """,
                             unsafe_allow_html=True)

        
        
with col3:
    st.markdown('[Data Disclaimer](https://gapsfinder.streamlit.app/pages/disclaimer.py)')
        
    


#%%


#  # Slider per gestire i parametri di ricerca
 
#  st.markdown("""
#     <style>
#     .slider-container {
#         width: 70%;  /* Modifica la larghezza secondo necessità */
#         margin: auto; /* Centrare il contenitore */
#         padding: 10px; /* Spazio interno per distanziare */
#     }
#     </style>
# """, unsafe_allow_html=True)

 
#  stampa_col2 = st.empty()
 
#  with stampa_col2.container():
     
#      st.markdown('<div class="slider-container">', unsafe_allow_html=True)
 
#      gap_A,gap_B = st.slider("Gap %",0,500,step=5,key='slider_gaps')
     
#      volume = st.slider("Volume Minimo Mln", 0,500,step=1,key='slider_volume')
     
#      prezzo_A,prezzo_B = st.slider('prezzo minimo $',0.0,500.0,step=0.5,key='slider_price')
     
#      st.markdown('</div>', unsafe_allow_html=True)
     
     
           
#      v_gaps = ricerca_gaps(nome_ticker,st.session_state['dati_storici'],\
#                                  st.session_state['trans'],gap_A,gap_B,volume*1_000_000,prezzo_A,prezzo_B) 
 
#  st.table(v_gaps)





#%%

# gap_A,gap_B = st.slider("Gap %",0,500,step=5,key='slider_gaps')

# volume = st.slider("Volume Minimo Mln", 0,500,step=1,key='slider_volume')

# prezzo_A,prezzo_B = st.slider('prezzo minimo $',0.0,500.0,step=0.5,key='slider_price')
      
# v_gaps = ricerca_gaps(nome_ticker,st.session_state['dati_storici'],\
#                             st.session_state['trans'],gap_A,gap_B,volume*1_000_000,prezzo_A,prezzo_B) 

# st.table(v_gaps)



#%%

# if not v_gaps.empty:
    
#     with col3:
        
#         col3_1,col3_2 = st.columns(1,3)
#         with col3_1:
            
#             options = list(v_gaps.index)
#             n_gap = st.selectbox('**gap da visualizzare**',options)
            
#         if st.button('visualizza'):
#         visual_gap(nome_ticker,(n_gap-1),st.session_state['dati_storici_ADJ'])



#%%


# with col2:
    
    
     
#     if 'dati_storici' in st.session_state and st.session_state['dati_storici'] is not None:
        
        

#             # Slider per gestire i parametri di ricerca


            
#             stampa_col2 = st.empty()
            
#             with stampa_col2.container():
                
#                 #st.markdown('<div class="slider-container">', unsafe_allow_html=True)
            
#                 gap_A,gap_B = st.slider("Gap %",0,500,step=5,key='slider_gaps')
                
#                 volume = st.slider("Volume Minimo Mln", 0,500,step=1,key='slider_volume')
                
#                 prezzo_A,prezzo_B = st.slider('prezzo minimo $',0.0,500.0,step=0.5,key='slider_price')
                
#                 #st.markdown('</div>', unsafe_allow_html=True)
                
                
                      
#                 v_gaps = ricerca_gaps(nome_ticker,st.session_state['dati_storici'],\
#                                             st.session_state['trans'],gap_A,gap_B,volume*1_000_000,prezzo_A,prezzo_B) 
            
#             st.table(v_gaps)









