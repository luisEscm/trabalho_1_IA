import matplotlib.pyplot as plt
import numpy as np
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
import random
import time
import os

pasta_save = "Projeto\\imagens dos resultados"
os.makedirs(pasta_save, exist_ok=True)
HOME = os.getcwd()
print(HOME)

def verificar_save_name(pasta_save_path, save_name):
    num_save = 1
    for _, subdirs, _ in os.walk(pasta_save_path):
        for dir in subdirs:
            num = int(dir.split("_")[0])
            #print(num)
            if num_save <= num:
                num_save = num+1
                #print(num_save)
            #print(num_save)
    
    save_final_name = f"{num_save}_{save_name}"
    pasta = os.path.join(pasta_save_path, save_final_name)
    print("+++++++++++++++++++")
    print(pasta)
    print("+++++++++++++++++++")
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    return save_final_name

class Item(Agent):
    def __init__(self, model, item_type, pontos):
        super().__init__(model)
        self.type = item_type
        self.pontos = pontos
        self.carregado_por = []

    def step(self):
        pass

def caminho_para_destino(posicao_atual, base, grid):
    """
    Calcula o caminho mais curto para a base.

    Args:
        posicao_atual (tuple): Posição atual do agente (x, y).
        base (tuple): Posição da base (x, y).
        grid: Objeto da grade (grid) do modelo.

    Returns:
        tuple: Próxima posição no caminho mais curto.
    """
    # Exemplo simples com movimentação Manhattan (não considera obstáculos neste exemplo).
    x_atual, y_atual = posicao_atual
    x_base, y_base = base
    #print(f"x_atual: {x_atual}")
    #print(f"x_base: {x_base}")
    #print(f"y_atual: {y_atual}")
    #print(f"y_base: {y_base}")
    # Movimenta no eixo X em direção à base, se necessário
    if x_atual < x_base:
        #return (x_atual + 1, y_atual)
        x_atual += 1
    elif x_atual > x_base:
        x_atual = x_atual - 1
        #return (x_atual - 1, y_atual)

    # Movimenta no eixo Y em direção à base, se necessário
    if y_atual < y_base:
        y_atual += 1
    elif y_atual > y_base:
        y_atual = y_atual - 1

    # Se já estiver na base, mantém a posição
    return (x_atual, y_atual)

class ReativoSimples(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.has_item = False
        self.item = None
        self.contribuicao = 0
        self.quant_entregue = 0
        self.nome = "AR"

    def pegar_item(self, item):
        if item is None:
            return
        if item.type == "Cristal Energético" or item.type == "Metal Raro":
            self.has_item = True
            self.item = item
            item.carregado_por = [self]

    def entregar_item(self):
        if self.has_item:
            self.contribuicao += self.item.pontos
            self.quant_entregue += 1

            self.has_item = False
            self.item.carregado_por = []
            self.model.remove_item(self.item)
            self.item = None

    def verificar_item(self, possiveis_passos):
        tem = False
        passo_ = None
        item = None
        for passo in possiveis_passos:
            itens = [obj for obj in self.model.grid.get_cell_list_contents([passo]) if isinstance(obj, Item)]
            for possivel_item in itens:
                if possivel_item.type != "Estrutura Antiga" and len(possivel_item.carregado_por) == 0:
                    tem = True
                    item = possivel_item
                    break
            if tem:
                passo_ = passo
                break
        return item, passo_

    def step(self):
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)

        if possible_steps:  # Se há posições disponíveis:
            if not self.has_item:  # Caso o agente não tenha um item:
                item, passo = self.verificar_item(possible_steps)  # Verifica por itens próximos.
            else:
                passo = None
                item = None

            # Define a nova posição do agente.
            if self.has_item:
                # Chama a função para determinar o próximo passo no caminho para a base
                #print(f"indo de:{self.pos}")
                new_position = caminho_para_destino(self.pos, self.model.base, self.model.grid) #base
                #print(f"para: {new_position}")
            elif passo is not None:
                new_position = passo
            else:
                # Caso contrário, o agente escolhe um passo aleatório (comportamento padrão)
                new_position = self.random.choice(possible_steps)

            self.model.grid.move_agent(self, new_position)

            if (not self.has_item) and (item is not None):
                self.pegar_item(item)


        if self.pos == self.model.base:
            self.entregar_item()

class AgentEstados(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.has_item = False
        self.item = None
        self.contribuicao = 0
        self.quant_entregue = 0
        self.nome = "AE"
        #self.memoria = np.full((model.grid.width, model.grid.height), "Desconhecido", dtype=object)  # Inicializa a memória com "Desconhecido".
    
    def pegar_item(self, item):
        if item.type == "Cristal Energético" or item.type == "Metal Raro":
            self.has_item = True
            self.item = item
            item.carregado_por = [self]

        elif item.type == "Estrutura Antiga" and len(item.carregado_por) < 2:
            item.carregado_por.append(self)
            if len(item.carregado_por) == 2:
                for agent in item.carregado_por:
                    agent.has_item = True
                    agent.item = item
        
    def entregar_item(self):
        if self.item:
            self.contribuicao += self.item.pontos
            self.quant_entregue += 1

            self.has_item = False
            self.item.carregado_por = []
            self.model.remove_item(self.item)
            self.item = None

    def verificar_item(self, possiveis_passos):
        tem = False
        passo_ = None
        item = None
        for passo in possiveis_passos:
            itens = [obj for obj in self.model.grid.get_cell_list_contents([passo]) if isinstance(obj, Item)]
            for possivel_item in itens:
                MEMORIA_COMPARTILHADA_AGENTES_ESTADO[passo[0]][passo[0]] = possivel_item.type
                if possivel_item.type != "Estrutura Antiga" and len(possivel_item.carregado_por) == 0:
                    tem = True
                    item = possivel_item
                    break
            if tem:
                passo_ = passo
                break
        return item, passo_
    
    def step(self):
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        posicao_antiga = self.pos

        # Atualiza a memória da posição antiga
        MEMORIA_COMPARTILHADA_AGENTES_ESTADO[posicao_antiga[0]][posicao_antiga[1]] = "Visitado"

        # Verifica se ainda há células desconhecidas na memória
        if not self.tem_area_desconhecida():
            print(f"Agente {self.unique_id}: Não há mais áreas desconhecidas para explorar. O agente parará.")
            return  # Parar o agente se não houver mais áreas desconhecidas

        if possible_steps:  # Se há passos vizinhos possíveis:
            if not self.has_item:  # Se o agente não está carregando um item:
                item, passo = self.verificar_item(possible_steps)  # Verifica itens nos passos vizinhos.
                # Atualiza a memória se encontrar um item
                #if item is not None:
                    #MEMORIA_COMPARTILHADA_AGENTES_ESTADO[item.pos[0]][item.pos[1]] = "Item"

            elif self.has_item:  # Se o agente está carregando um item:
                #print('Tá com item')
                passo = caminho_para_destino(self.pos, self.model.base, self.model.grid)  # Calcula o caminho para a base.

            else:
                #print('passo NONE')
                passo = None  # Não há passo específico para buscar itens.
                item = None  # Não há item a ser carregado.

            # Se nenhum passo foi definido, aplica o filtro para evitar revisitar posições
            if passo is None:
                # Filtra possíveis passos para evitar revisitar posições conhecidas
                possiveis_passos_nao_visitados = [
                    p for p in possible_steps if MEMORIA_COMPARTILHADA_AGENTES_ESTADO[p[0]][p[1]] == "Desconhecido"
                ]
                if not possiveis_passos_nao_visitados:  # Se todos já foram visitados
                    print("Buscando globalmente uma posição desconhecida.")
                    destino_global = self.encontrar_desconhecido_mais_proximo(self.pos,
                                                                              MEMORIA_COMPARTILHADA_AGENTES_ESTADO)
                    if destino_global:
                        #print(f"Agente {self.unique_id}: Calculando caminho para {destino_global}.")
                        passo = caminho_para_destino(self.pos, destino_global,
                                                     self.model.grid)  # Usando a função para ir ao destino
                    else:
                        possiveis_passos_nao_visitados = possible_steps  # Considera todos os passos disponíveis.
                else:
                    passo = self.random.choice(possiveis_passos_nao_visitados)  # Escolhe entre os não visitados.

            # Prioriza o movimento para o passo encontrado
            new_position = passo if passo is not None else self.random.choice(possible_steps)

            #print('Set nova posição:', new_position)  # Atualiza a posição do agente
            self.model.grid.move_agent(self, new_position)
            self.exibir_memoria()  # Exibe a memória após cada movimento

            if not self.has_item and item is not None:
                self.pegar_item(item)

        # Atualiza a memória ao alcançar a base
        if self.pos == self.model.base:
            MEMORIA_COMPARTILHADA_AGENTES_ESTADO[self.pos[0]][self.pos[1]] = "Base"
            self.entregar_item()

    def tem_area_desconhecida(self):
        """
        Verifica se ainda há células desconhecidas na memória.

        Returns:
            bool: Retorna True se houver células desconhecidas, False caso contrário.
        """
        for linha in MEMORIA_COMPARTILHADA_AGENTES_ESTADO:
            if "Desconhecido" in linha:  # Verifica se há algum valor "Desconhecido" em qualquer célula
                return True
        return False
    
    def encontrar_desconhecido_mais_proximo(self, posicao_atual, memoria):
        """
        Busca globalmente a célula desconhecida mais próxima na memória compartilhada.

        Args:
            posicao_atual (tuple): Posição atual do agente (x, y).
            memoria (numpy.ndarray): Matriz de memória compartilhada.

        Returns:
            tuple: Coordenadas (x, y) da célula desconhecida mais próxima ou None se não houver.
        """
        from collections import deque

        fila = deque([posicao_atual])
        visitados = set()
        visitados.add(posicao_atual)

        while fila:
            atual = fila.popleft()
            x, y = atual

            # Verifica se a célula atual é desconhecida
            if memoria[x][y] == "Desconhecido":
                return atual

            # Adiciona vizinhos na fila
            vizinhos = [
                (nx, ny) for nx, ny in [
                    (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)
                ]
                if 0 <= nx < memoria.shape[0] and 0 <= ny < memoria.shape[1] and (nx, ny) not in visitados
            ]

            fila.extend(vizinhos)
            visitados.update(vizinhos)

        return None  # Retorna None se nenhuma célula desconhecida for encontrada
    
    def exibir_memoria(self):
        """
        Exibe a matriz de memória compartilhada de forma organizada, utilizando o formato cartesiano.
        """
        print("Memória Compartilhada Atual:")

        for y in range(MEMORIA_COMPARTILHADA_AGENTES_ESTADO.shape[1] - 1, -1,
                       -1):  # Inverte a ordem no eixo Y para simular a visualização cartesiana (0,0 no canto inferior esquerdo)
            linha = ""
            for x in range(MEMORIA_COMPARTILHADA_AGENTES_ESTADO.shape[0]):
                estado = MEMORIA_COMPARTILHADA_AGENTES_ESTADO[x][y]
                linha += f"({y},{x}): {estado: <12} "  # Exibe a posição (x, y) e o estado
            print(linha)

class AgenteBaseadoEmObjetivos2(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.has_item = False
        self.item = None
        self.contribuicao = 0
        self.quant_entregue = 0
        self.nome = "ABO"
        self.conhece_itens = []  # Inicializa a lista de itens conhecidos vazia
        self.emBuscaPor = None
        self.objetivo_info = None
        self.memoria = np.full((model.grid.width, model.grid.height), "Desconhecido", dtype=object)

    def atualizar_informacoes_ambiente(self):
        """
        Atualiza a lista de objetivos com base nos itens "livres" e que estão registrados
        pelo agente BDI, e a memoria de visitados com base nos outros agentes.
        """
        bdi = self.model.bdi 
        lista_itens_ocupados = []
        posicoes = []
        for agent in self.model.schedule.agents:
            if isinstance(agent, AgenteBaseadoEmObjetivos2) and isinstance(agent, AgenteCooperativo):
                if agent.objetivo_info != None and agent.objetivo_info != "Base":
                    lista_itens_ocupados.append(agent.objetivo_info[0])
            posicoes.append(agent.pos)


        conhece_itens_temp = [obj for obj in bdi.recursos]
        self.conhece_itens = conhece_itens_temp
        print(self.conhece_itens)
        print(lista_itens_ocupados)

        for item in conhece_itens_temp:
            if "EA" in item[0] and lista_itens_ocupados.count(item[0]) >=2:
                self.conhece_itens.remove(item)
            elif item[0] in lista_itens_ocupados:
                self.conhece_itens.remove(item)

        for (px, py) in posicoes:
             self.memoria[px][py] = "Visitado"
        print(self.conhece_itens)

    def pegar_item(self, item):
        """
        Função que pega um item
        Args:
            item (Item): item a ser pego pelo agente
        """
        if item.type == "Cristal Energético" or item.type == "Metal Raro":
            self.has_item = True
            self.item = item
            item.carregado_por = [self]
            self.objetivo_info = "Base"

        elif item.type == "Estrutura Antiga" and len(item.carregado_por) < 2:
            item.carregado_por.append(self)
            #if len(item.carregado_por) == 2:
                #for agent in item.carregado_por:
            self.has_item = True
            self.item = item
            self.objetivo_info = "Base"
        self.model.bdi.recurso_coletado(item)

    def entregar_item(self):
        if self.item:
            self.contribuicao += self.item.pontos
            self.quant_entregue += 1

            if self.item.type != "Estrutura Antiga":
                self.has_item = False
                self.item.carregado_por = []
                self.model.remove_item(self.item)
                self.item = None
                self.emBuscaPor = None
                self.objetivo_info = None
            
            elif self.item.type == "Estrutura Antiga":
                
                carregadores = self.item.carregado_por
                colega = self
                print(carregadores)
                for carry in carregadores:
                    if carry.unique_id != self.unique_id:
                        colega = carry
                        break

                if colega.pos == self.pos:
                    self.item.carregado_por.clear()

                if not self.item.carregado_por:
                    self.model.remove_item(self.item)
                
                print(carregadores)
                
                self.item = None
                self.has_item = False
                self.emBuscaPor = None
                self.objetivo_info = None

    def encontrar_desconhecido_mais_proximo(self, posicao_atual, memoria):
        """
        Busca globalmente a célula desconhecida mais próxima na memória compartilhada.

        Args:
            posicao_atual (tuple): Posição atual do agente (x, y).
            memoria (numpy.ndarray): Matriz de memória compartilhada.

        Returns:
            tuple: Coordenadas (x, y) da célula desconhecida mais próxima ou None se não houver.
        """
        from collections import deque

        fila = deque([posicao_atual])
        visitados = set()
        visitados.add(posicao_atual)

        while fila:
            atual = fila.popleft()
            x, y = atual

            # Verifica se a célula atual é desconhecida
            if memoria[x][y] == "Desconhecido":
                return atual

            # Adiciona vizinhos na fila
            vizinhos = [
                (nx, ny) for nx, ny in [
                    (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)
                ]
                if 0 <= nx < memoria.shape[0] and 0 <= ny < memoria.shape[1] and (nx, ny) not in visitados
            ]

            fila.extend(vizinhos)
            visitados.update(vizinhos)

        return None  # Retorna None se nenhuma célula desconhecida for encontrada

    def procurar_itens(self, possiveis_passos):
        """
        Função para procurar por itens ainda não conhecidos evitando revisitar posições que ja tenha visitado
        Args:
            possiveis_passos (list): lista dos passos que podem ser tomados pelo agente
        Returns:
            tuple: coordenadas do proximo passo a ser tomado no formato (x, y)
        """
        possiveis_passos_nao_visitados = [
            p for p in possiveis_passos if self.memoria[p[0]][p[1]] == "Desconhecido"
        ]
        #print(possiveis_passos_nao_visitados)

        if not possiveis_passos_nao_visitados:  # Se todos já foram visitados
            print("Buscando globalmente uma posição desconhecida.")
            destino_global = self.encontrar_desconhecido_mais_proximo(self.pos,
                                                                        self.memoria)
            if destino_global:
                proxima_posicao = caminho_para_destino(self.pos, destino_global,
                                                self.model.grid)  # Usando a função para ir ao destino
            else:
                possiveis_passos_nao_visitados = possiveis_passos  # Considera todos os passos disponíveis.
        else:
            proxima_posicao = self.random.choice(possiveis_passos_nao_visitados)  # Escolhe entre os não visitados.
        
        return proxima_posicao

    def buscar_objetivo(self):
        """
        Função que escolhe um objetivo se não tiver um, e anda na direção do objetivo
        Returns:
            tuple: coordenadas do proximo passo a ser tomado pelo agente no formato (x, y)
        """
        item_mais_proximo = None

        itens_disponiveis = self.conhece_itens
        print('buscando por:', self.unique_id,' ', self.emBuscaPor)
        print('itens_disponiveis:',self.unique_id,' ', itens_disponiveis)


        if itens_disponiveis and self.emBuscaPor is None:
            # pega o primeiro item disponivel na lista de objetivos
            item_mais_proximo = itens_disponiveis[0]

            proxima_posicao = caminho_para_destino(self.pos, item_mais_proximo[1], self.model.grid)

            self.objetivo_info = item_mais_proximo
            self.emBuscaPor = item_mais_proximo[1]


        elif self.emBuscaPor is not None:
            proxima_posicao = caminho_para_destino(self.pos, self.emBuscaPor,
                                                    self.model.grid)

        else:
            print('Fazendo nada')
            proxima_posicao = self.pos

        return proxima_posicao

    def voltar_base(self):
        """
        Função que faz o agente voltar para base caso tenha um item com ele, caso seja estrutura antiga só
        anda se houver um outro agente segurando o item.
        Returns:
            tuple: coordenadas do proximo passo a ser tomado pelo agente no formato (x, y)
        """
        proximo_passo = self.pos

        if self.has_item:
            item = self.item
            if item.type == "Estrutura Antiga":
                if len(item.carregado_por) < 2:
                    return proximo_passo
                
                colega_pos = self.pos
                
                for carry in item.carregado_por:
                    if carry.unique_id != self.unique_id and carry.objetivo_info == "Base":
                        colega_pos = carry.pos
                        print(colega_pos)

                print(colega_pos)
                if colega_pos == self.pos: #TODO considerar se deve literalmente andar estando no mesmo bloco
                                           # se sim temos de fazer um logica para que se movam 1 só vez no step
                                           # e não duas tipo ao inves de um dar o passo e o outro dar um passo 
                                           # depois, um dos dois controla o passo dos dois assim fazem um "step" 
                                           # pelos dois
                    proximo_passo = caminho_para_destino(self.pos, self.model.base, self.model.grid)
                else:
                    proximo_passo = colega_pos
            else:
                proximo_passo = caminho_para_destino(self.pos, self.model.base, self.model.grid)
            
        return proximo_passo

    def step(self):
        print(f"__________________________________{self.nome}{self.unique_id}__________________________________")
        possiveis_passos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        if self.model.tem_bdi:
            self.model.bdi.localizar_itens(possiveis_passos)

        # Atualiza os itens conhecidos no início de cada passo
        self.atualizar_informacoes_ambiente()
        proxima_posicao = self.pos
        print(f"{self.nome}{self.unique_id} condição: {self.has_item}")

        if not self.has_item:
            # Planeja ir até o item marcado como objetivo
            if self.conhece_itens or self.emBuscaPor is not None:

                proxima_posicao = self.buscar_objetivo()

            else:
                proxima_posicao = self.procurar_itens(possiveis_passos=possiveis_passos)
                
        else:
            # Se está carregando um item, vai para a base
            proxima_posicao = self.voltar_base()
            #proxima_posicao = caminho_para_destino(self.pos, self.model.base, self.model.grid)

        # Move o agente para a próxima posição
        print('--                                 --')
        self.memoria[self.pos[0]][self.pos[1]] = "Visitado"
        self.model.grid.move_agent(self, proxima_posicao)

        # Entrega o item ao chegar na base
        if self.pos == self.model.base and self.has_item:
            self.entregar_item()
        elif self.pos == self.emBuscaPor and not self.has_item:
            itens_na_posicao = self.model.grid.get_cell_list_contents([self.pos])
            for obj in itens_na_posicao:
                if isinstance(obj, Item):
                    self.pegar_item(obj)

class AgenteBaseadoEmObjetivos(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.has_item = False
        self.item = None
        self.contribuicao = 0
        self.nome = "ABO"
        self.conhece_itens = []  # Inicializa a lista de itens conhecidos vazia
        self.emBuscaPor = None
        self.memoria = np.full((model.grid.width, model.grid.height), "Desconhecido", dtype=object)

    def atualizar_informacoes_ambiente(self):
        """
        Atualiza a lista de itens conhecidos com base no estado atual do grid.
        """
        estado_grid = self.model.obter_estado_grid()  # Solicita o estado do grid ao modelo
        self.conhece_itens = [
            item for item in estado_grid if item['tipo'] in ["Cristal Energético", "Metal Raro", "Estrutura Antiga"]
        ]

    def pegar_item(self, item):
        if item.type == "Cristal Energético" or item.type == "Metal Raro":
            self.has_item = True
            self.item = item
            item.carregado_por = [self]

        elif item.type == "Estrutura Antiga" and len(item.carregado_por) < 2:
            item.carregado_por.append(self)
            if len(item.carregado_por) == 2:
                for agent in item.carregado_por:
                    agent.has_item = True
                    agent.item = item

    def entregar_item(self):
        if self.item:
            self.contribuicao += self.item.pontos

            self.has_item = False
            self.item.carregado_por = []
            self.model.remove_item(self.item)
            self.item = None
            self.emBuscaPor = None

    def step(self):
        # Atualiza os itens conhecidos no início de cada passo
        self.atualizar_informacoes_ambiente()
        if self.model.tem_bdi:
            possiveis_passos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
            self.model.bdi.localizar_itens(possiveis_passos)

        if not self.has_item:
            # Planeja ir até o item mais próximo
            if self.conhece_itens :

                # Inicializa uma variável para guardar o item mais próximo
                item_mais_proximo = None

                # Filtra apenas itens cuja posição ainda não está na memória compartilhada


                itens_disponiveis = [
                    item for item in self.conhece_itens
                    if item['tipo'] in ["Cristal Energético", "Metal Raro"] and
                       item['posicao'] not in self.model.memoria_compartilhadaAgenteObjetivo
                ]
                print('buscando por:', self.unique_id,' ', itens_disponiveis)
                print('itens_disponiveis:',self.unique_id,' ', itens_disponiveis)
                print('memoria_compartilhadaAgenteObjetivo:',self.unique_id,' ', self.model.memoria_compartilhadaAgenteObjetivo)


                if itens_disponiveis and self.emBuscaPor is None:
                    item_mais_proximo = min(
                        itens_disponiveis,
                        key=lambda item: abs(item['posicao'][0] - self.pos[0]) + abs(item['posicao'][1] - self.pos[1])
                    )

                    proxima_posicao = caminho_para_destino(self.pos, item_mais_proximo['posicao'], self.model.grid)

                    # Adiciona o item mais próximo à memória compartilhada
                    self.model.memoria_compartilhadaAgenteObjetivo.append(item_mais_proximo['posicao'])
                    self.emBuscaPor = item_mais_proximo['posicao']
                    print(f"Item na posição {item_mais_proximo['posicao']} adicionado à memória compartilhada.")


                elif self.emBuscaPor is not None:
                    print(' Tem obj:')
                    # Se chegou ao item, tenta pegá-lo
                    if self.pos == self.emBuscaPor:
                        itens_na_posicao = self.model.grid.get_cell_list_contents([self.pos])
                        for obj in itens_na_posicao:
                            if isinstance(obj, Item):
                                self.pegar_item(obj)
                                proxima_posicao = caminho_para_destino(self.pos, self.model.base, self.model.grid)
                    else:
                        proxima_posicao = caminho_para_destino(self.pos, self.emBuscaPor,
                                                               self.model.grid)


                else:
                    print('Fazendo nada')
                    return 0

            else:
                print('Fazendo nada')
                return 0

        else:
            # Se está carregando um item, vai para a base
            proxima_posicao = caminho_para_destino(self.pos, self.model.base, self.model.grid)

        # Move o agente para a próxima posição
        print('--                                 --')
        self.model.grid.move_agent(self, proxima_posicao)

        # Entrega o item ao chegar na base
        if self.pos == self.model.base:
            self.entregar_item()

#TODO verificar se realmente esta funcionando em todos os casos, provalmente esta
# mas não tenho 100% de certeza
class AgenteCooperativo(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.has_item = False
        self.item = None
        self.contribuicao = 0
        self.quant_entregue = 0
        self.nome = "ACO"
        self.conhece_itens = []  # Inicializa a lista de itens conhecidos vazia
        self.emBuscaPor = None
        self.objetivo_info = None
        self.memoria = np.full((model.grid.width, model.grid.height), "Desconhecido", dtype=object)

    def atualizar_informacoes_ambiente(self):
        """
        Atualiza a lista de objetivos com base nos itens "livres" e que estão registrados
        pelo agente BDI, e a memoria de visitados com base nos outros agentes.
        """
        bdi = self.model.bdi 
        lista_itens_ocupados = []
        #distancias = []
        posicoes = []
        px, py = self.pos
        bx, by = self.model.base

        for agent in self.model.schedule.agents:
            if isinstance(agent, AgenteBaseadoEmObjetivos2) or isinstance(agent, AgenteBaseadoEmObjetivos2):
                if agent.objetivo_info != None and agent.objetivo_info != "Base":
                    lista_itens_ocupados.append(agent.objetivo_info[0])
                posicoes.append(agent.pos)

                        # nome+unique_id do item | posição do item | distancia agente para item | distancia item para base
        conhece_itens_temp = [(obj_nome, obj_pos, abs(obj_pos[0] - px) + abs(obj_pos[1] - py),
                               (abs(obj_pos[0] - bx) + abs(obj_pos[1] - by))) for obj_nome, obj_pos in bdi.recursos]
        self.conhece_itens = conhece_itens_temp
        print(f"itens conhecidos 1: {self.conhece_itens}")
        #print(lista_itens_ocupados)

        for item in conhece_itens_temp:
            if "EA" in item[0] and lista_itens_ocupados.count(item[0]) >=2:
                self.conhece_itens.remove(item)

            elif item[0] in lista_itens_ocupados:
                self.conhece_itens.remove(item)

        for (px, py) in posicoes:
             self.memoria[px][py] = "Visitado"
        print(f"itens conhecidos 1: {self.conhece_itens}")

    def pegar_item(self, item):
        """
        Função que pega um item
        Args:
            item (Item): item a ser pego pelo agente
        """
        if item.type == "Cristal Energético" or item.type == "Metal Raro":
            self.has_item = True
            self.item = item
            item.carregado_por = [self]
            self.objetivo_info = "Base"

        elif item.type == "Estrutura Antiga" and len(item.carregado_por) < 2:
            item.carregado_por.append(self)
            #if len(item.carregado_por) == 2:
                #for agent in item.carregado_por:
            self.has_item = True
            self.item = item
            self.objetivo_info = "Base"
        self.model.bdi.recurso_coletado(item)

    def entregar_item(self):
        if self.item:
            self.contribuicao += self.item.pontos
            self.quant_entregue += 1

            if self.item.type != "Estrutura Antiga":
                self.has_item = False
                self.item.carregado_por = []
                self.model.remove_item(self.item)
                self.item = None
                self.emBuscaPor = None
                self.objetivo_info = None
            
            elif self.item.type == "Estrutura Antiga":
                
                carregadores = self.item.carregado_por
                colega = self
                print(carregadores)
                for carry in carregadores:
                    if carry.unique_id != self.unique_id:
                        colega = carry
                        break

                if colega.pos == self.pos:
                    self.item.carregado_por.clear()

                if not self.item.carregado_por:
                    self.model.remove_item(self.item)
                
                print(carregadores)
                
                self.item = None
                self.has_item = False
                self.emBuscaPor = None
                self.objetivo_info = None

    def encontrar_desconhecido_mais_proximo(self, posicao_atual, memoria):
        """
        Busca globalmente a célula desconhecida mais próxima na memória compartilhada.

        Args:
            posicao_atual (tuple): Posição atual do agente (x, y).
            memoria (numpy.ndarray): Matriz de memória compartilhada.

        Returns:
            tuple: Coordenadas (x, y) da célula desconhecida mais próxima ou None se não houver.
        """
        from collections import deque

        fila = deque([posicao_atual])
        visitados = set()
        visitados.add(posicao_atual)

        while fila:
            atual = fila.popleft()
            x, y = atual

            # Verifica se a célula atual é desconhecida
            if memoria[x][y] == "Desconhecido":
                return atual

            # Adiciona vizinhos na fila
            vizinhos = [
                (nx, ny) for nx, ny in [
                    (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)
                ]
                if 0 <= nx < memoria.shape[0] and 0 <= ny < memoria.shape[1] and (nx, ny) not in visitados
            ]

            fila.extend(vizinhos)
            visitados.update(vizinhos)

        return None  # Retorna None se nenhuma célula desconhecida for encontrada

    def procurar_itens(self, possiveis_passos):
        """
        Função para procurar por itens ainda não conhecidos evitando revisitar posições que ja tenha visitado
        Args:
            possiveis_passos (list): lista dos passos que podem ser tomados pelo agente
        Returns:
            tuple: coordenadas do proximo passo a ser tomado no formato (x, y)
        """
        possiveis_passos_nao_visitados = [
            p for p in possiveis_passos if self.memoria[p[0]][p[1]] == "Desconhecido"
        ]
        #print(possiveis_passos_nao_visitados)

        if not possiveis_passos_nao_visitados:  # Se todos já foram visitados
            print("Buscando globalmente uma posição desconhecida.")
            destino_global = self.encontrar_desconhecido_mais_proximo(self.pos,
                                                                        self.memoria)
            if destino_global:
                proxima_posicao = caminho_para_destino(self.pos, destino_global,
                                                self.model.grid)  # Usando a função para ir ao destino
            else:
                possiveis_passos_nao_visitados = possiveis_passos  # Considera todos os passos disponíveis.
        else:
            proxima_posicao = self.random.choice(possiveis_passos_nao_visitados)  # Escolhe entre os não visitados.
        
        return proxima_posicao

    def buscar_objetivo(self):
        """
        Função que escolhe um objetivo se não tiver um, e anda na direção do objetivo
        Returns:
            tuple: coordenadas do proximo passo a ser tomado pelo agente no formato (x, y)
        """
        item_mais_proximo = None

        itens_disponiveis = self.conhece_itens
        print('buscando por:', self.unique_id,' ', self.emBuscaPor)
        print('itens_disponiveis:',self.unique_id,' ', itens_disponiveis)


        if itens_disponiveis and self.emBuscaPor is None:
            # pega o primeiro item disponivel na lista de objetivos
            self.considerar_objetivo()
            item_mais_proximo = self.objetivo_info

            proxima_posicao = caminho_para_destino(self.pos, item_mais_proximo[1], self.model.grid)

            self.objetivo_info = item_mais_proximo
            self.emBuscaPor = item_mais_proximo[1]


        elif self.emBuscaPor is not None:
            proxima_posicao = caminho_para_destino(self.pos, self.emBuscaPor,
                                                    self.model.grid)

        else:
            print('Fazendo nada')
            proxima_posicao = self.pos

        return proxima_posicao

    def voltar_base(self):
        """
        Função que faz o agente voltar para base caso tenha um item com ele, caso seja estrutura antiga só
        anda se houver um outro agente segurando o item.
        Returns:
            tuple: coordenadas do proximo passo a ser tomado pelo agente no formato (x, y)
        """
        proximo_passo = self.pos

        if self.has_item:
            item = self.item
            if item.type == "Estrutura Antiga":
                if len(item.carregado_por) < 2:
                    return proximo_passo
                
                colega_pos = self.pos
                
                for carry in item.carregado_por:
                    if carry.unique_id != self.unique_id and carry.objetivo_info == "Base":
                        colega_pos = carry.pos
                        print(colega_pos)

                print(colega_pos)
                if colega_pos == self.pos:
                    proximo_passo = caminho_para_destino(self.pos, self.model.base, self.model.grid)
                else:
                    proximo_passo = colega_pos
            else:
                proximo_passo = caminho_para_destino(self.pos, self.model.base, self.model.grid)
            
        return proximo_passo

    def considerar_objetivo(self):
        print(f"considerando Objetivo: {self.objetivo_info}")
        bx, by = self.model.base
        px, py = self.pos
        bdi = self.model.bdi
        info_objetivo = self.objetivo_info
        if info_objetivo == "Base":
            return
        quant_objetivo_atual = 0
        objetivos = {}
        posicoes = []
        for agent in self.model.schedule.agents:
            if isinstance(agent,AgenteCooperativo):

                if agent.objetivo_info != None and agent.objetivo_info != "Base":
                    print(f"tem chave no dict: {objetivos.get(agent.objetivo_info[0])}")
                    print(f"chave: {agent.objetivo_info}")

                    if objetivos.get(agent.objetivo_info[0]) is None:
                        objetivos[agent.objetivo_info[0]] = []

                    objetivos[agent.objetivo_info[0]].append((agent, agent.objetivo_info[2]))

                    if agent.objetivo_info[0] == info_objetivo:
                        quant_objetivo_atual += 1
                posicoes.append((agent, agent.pos))

            elif isinstance(agent, AgenteBaseadoEmObjetivos2):
                if agent.objetivo_info != None and agent.objetivo_info != "Base":
                    print(f"tem chave no dict: {objetivos.get(agent.objetivo_info[0])}")
                    print(f"chave: {agent.objetivo_info}")

                    if objetivos.get(agent.objetivo_info[0]) is None:
                        objetivos[agent.objetivo_info[0]] = []
                    
                    posicao_item = bdi.posicao_item(agent.objetivo_info[0])
                    if posicao_item is not None:
                        tx, ty = posicao_item
                    else:
                        tx, ty = agent.pos
                    px_temp, py_temp = agent.pos
                    dist = abs(tx - px_temp) + abs(ty - py_temp)
                    objetivos[agent.objetivo_info[0]].append((agent, dist))

                    if agent.objetivo_info[0] == info_objetivo:
                        quant_objetivo_atual += 1
                posicoes.append((agent, agent.pos))

        if info_objetivo is not None and objetivos.get(info_objetivo[0]) is not None:
            info = objetivos[info_objetivo[0]]
            if len(info) > 2 and "EA" in info_objetivo[0]:
                menor = (self, self.objetivo_info[2])
                for agent_info in info:
                    if agent_info[1] < menor[1]:
                        menor = agent_info
                
                if menor[0].unique_id != self.unique_id:
                    self.objetivo_info = None
                    self.emBuscaPor = None

        # atualizando objetivo
        if info_objetivo is not None:
            estruturas_antigas = [(obj_nome, obj_pos, abs(obj_pos[0] - px) + abs(obj_pos[1] - py),
                                (abs(obj_pos[0] - bx) + abs(obj_pos[1] - by))) for obj_nome, obj_pos in bdi.recursos if "EA" in obj_pos]
            
            dist_total_atual = info_objetivo[2] + info_objetivo[3]
            valor = 10

            if "EA" in info_objetivo[0]:
                valor = 50
            elif "MR" in info_objetivo[1]:
                valor = 20

            for estrutura in estruturas_antigas:
                if objetivos.get(estrutura[0]) is not None:
                    info = objetivos[estrutura[0]]
                    if len(info) >= 2:
                        continue

                    segundo_agente = None
                    mais_distante = (self, estrutura[2])
                    terceiro_agente = None
                    for info_agent in info:
                        if info_agent[1] > mais_distante[1]:
                            mais_distante = info_agent
                            segundo_agente = info_agent
                        
                        if segundo_agente is None or segundo_agente == mais_distante:
                            segundo_agente = info_agent

                        elif terceiro_agente is None:
                            terceiro_agente = info_agent

                    # agente atual é dos 3 agentes o mais distante do objeto então escolhe não ir
                    if mais_distante[0].unique_id == self.unique_id and len(info) >= 2:
                        continue

                    # agente ou é o de distancia média ou o de menor distancia
                    terceiro_agente = (self, estrutura[2])
                    
                    dist_total = mais_distante[1] + estrutura[3]
                    custo = min(round((50 - valor)/10), 6)

                    agente_distante = mais_distante[0]
                    # calcula o custo de se vale mais apenas ir atras do seu objetivo ou ir atras de um objetivo mais próximo
                    if dist_total < dist_total_atual+custo:
                        self.objetivo_info = estrutura
                        self.emBuscaPor = estrutura[1]

                        if len(info) >= 2:
                            agente_distante.objetivo_info = None
                            agente_distante.emBuscaPor = None

                        quant_objetivo_atual = 2

                    # Se o valor de custo for igual verifica se ele está sosinho ou não se estiver vai ajudar, caso o valor
                    # seja maior, considera que é melhor ir atras do que estava buscando e ajudar depois
                    elif dist_total == dist_total_atual and len(info) < 2:
                        self.objetivo_info = estrutura
                        self.emBuscaPor = estrutura[1]
                        quant_objetivo_atual = 2

                    # se estiver indo até uma estrutura antiga sosinho e a outra estiver com alguem ele vai atrasd da outra estrutura
                    elif "EA" in self.objetivo_info[0] and len(info) < 2 and quant_objetivo_atual < 2:
                        self.objetivo_info = estrutura
                        self.emBuscaPor = estrutura[1]
                        quant_objetivo_atual = 2

        else:
            objetivos_agent = [(obj_nome, obj_pos, abs(obj_pos[0] - px) + abs(obj_pos[1] - py),
                            (abs(obj_pos[0] - bx) + abs(obj_pos[1] - by))) for obj_nome, obj_pos in bdi.recursos]
            
            objetivo_custo_benef = None
            for objetivo in objetivos_agent:
                if objetivo_custo_benef is None:
                    
                    if objetivos.get(objetivo[0]) is None:
                        objetivo_custo_benef = objetivo
                    
                    elif "EA" in objetivo[0] and len(objetivos[objetivo[0]]) < 2:
                        objetivo_custo_benef = objetivo
                
                else:
                    if ("EA" not in objetivo[0] and objetivos.get(objetivo[0]) is not None):
                        continue

                    elif "EA" in objetivo[0]:
                        if objetivos.get(objetivo[0]) is not None:
                            info = objetivos[objetivo[0]]
                            if len(info) >= 2:
                                continue
                            agente_atras_obj = info[0]
                            mais_proximo = (self, objetivo[2])
                            tx, ty = objetivo[1]
                            for posicao in posicoes:
                                if posicao[0].unique_id != agente_atras_obj[0].unique_id:
                                    px_temp, py_temp = posicao[1]

                                    dist = (tx - px_temp) + (ty - py_temp)
                                    if dist < mais_proximo:
                                        mais_proximo = (posicao[0], dist)
                            
                            if mais_proximo[0].unique_id != self.unique_id:
                                continue

                            valor = 10 # valor no sentido de peso, é possivel aumentalo em prol de ajustar o custo beneficio
                            if "EA" in objetivo_custo_benef[0]:
                                valor = 50
                            elif "MR" in objetivo_custo_benef[0]:
                                valor = 20
                            
                            custo = min(round((50 - valor)/10), 6)
                            dist_total_1 = objetivo_custo_benef[2] + objetivo_custo_benef[3] # objetivo escolhido até o momento
                            dist_total_2 = objetivo[2] + objetivo[3] # objetivo sendo avaliado

                            if dist_total_2 < dist_total_1+custo:
                                objetivo_custo_benef = objetivo

                            elif dist_total_2 == dist_total_1+custo:
                                if "EA" not in objetivo_custo_benef[0]:
                                    objetivo_custo_benef = objetivo
                                elif objetivos.get(objetivo_custo_benef[0]) is None:
                                    objetivo_custo_benef = objetivo
                            
                            elif "EA" in objetivo_custo_benef[0] and objetivos.get(objetivo_custo_benef[0]) is None:
                                objetivo_custo_benef = objetivo
                    
                    else:
                        dist_obj = objetivo[2] + objetivo[3]
                        dist_custo_benef = objetivo_custo_benef[2] + objetivo_custo_benef[3]

                        valor_obj = 10
                        valor_custo_benef = 10

                        if "MR" in objetivo[0]:
                            valor_obj = 20
                        
                        if "MR" in objetivo_custo_benef[0]:
                            valor_custo_benef = 20
                        elif "EA" in objetivo_custo_benef[0]:
                            valor_custo_benef = 50

                        custo = min(round((valor_obj - valor_custo_benef)/10),6)
                        # custo sempre vai para a distancia do objeto que não é EA para fazer a comparação
                        if dist_obj < dist_custo_benef+custo:
                            objetivo_custo_benef = objetivo
                        elif "EA" not in objetivo_custo_benef[0] and dist_obj == dist_custo_benef:
                            if valor_obj > valor_custo_benef:
                                objetivo_custo_benef = objetivo

                        elif "EA" in objetivo_custo_benef[0] and objetivos.get(objetivo_custo_benef[0]) is not None:
                            continue
            self.objetivo_info = objetivo_custo_benef
            self.emBuscaPor = objetivo_custo_benef[1]

        print(f"Objetivo considerado: {self.objetivo_info}")

    def step(self):
        print(f"__________________________________{self.nome}{self.unique_id}__________________________________")
        possiveis_passos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        if self.model.tem_bdi:
            self.model.bdi.localizar_itens(possiveis_passos)

        # Atualiza os itens conhecidos no início de cada passo
        self.atualizar_informacoes_ambiente()
        proxima_posicao = self.pos
        print(f"{self.nome}{self.unique_id} condição: {self.has_item}")

        if not self.has_item:
            # Planeja ir até o item marcado como objetivo
            print(f"Objetivo: {self.objetivo_info}")
            if self.conhece_itens or self.emBuscaPor is not None:
                self.considerar_objetivo()
                proxima_posicao = self.buscar_objetivo()

            else:
                proxima_posicao = self.procurar_itens(possiveis_passos=possiveis_passos)
                
        else:
            # Se está carregando um item, vai para a base
            proxima_posicao = self.voltar_base()
            #proxima_posicao = caminho_para_destino(self.pos, self.model.base, self.model.grid)

        # Move o agente para a próxima posição
        print('--                                 --')
        self.memoria[self.pos[0]][self.pos[1]] = "Visitado"
        self.model.grid.move_agent(self, proxima_posicao)

        # Entrega o item ao chegar na base
        if self.pos == self.model.base and self.has_item:
            self.entregar_item()
        elif self.pos == self.emBuscaPor and not self.has_item:
            itens_na_posicao = self.model.grid.get_cell_list_contents([self.pos])
            for obj in itens_na_posicao:
                if isinstance(obj, Item):
                    self.pegar_item(obj)


class AgentBDI(Agent):
    def __init__(self, model):
        super().__init__(model)
        #self.has_item = False
        #self.item = None
        self.contribuicao = 0
        self.quant_entregue = 0
        self.nome = "AB"
        self.agentes_pos = {}
        self.recursos = []

    def localizar_itens(self, possiveis_passos):
        #item = []
        for passo in possiveis_passos:
            itens = [obj for obj in self.model.grid.get_cell_list_contents([passo]) if isinstance(obj, Item)]
            for item in itens:
                if item.type != "Estrutura Antiga" and len(item.carregado_por) >= 1:
                    continue
                elif item.type == "Cristal Energético":
                    nome = 'CE'
                elif item.type == "Metal Raro":
                    nome = 'MR'
                elif item.type == "Estrutura Antiga" and len(item.carregado_por) < 2:
                    nome = 'EA'
                elif item.type == "Estrutura Antiga" and len(item.carregado_por) >= 2:
                    continue
                else:
                    nome = 'I'

                item_info = (nome + str(item.unique_id), item.pos)
                if item_info not in self.recursos:
                    self.recursos.append(item_info)
    
    def recurso_coletado(self, item):
        """
        remove um recurso da lista quando é coletado.

        Args:
            item (Item): item a ser removido da lista de objetivos do bdi.
        """
        if item != None:
            if item.type == "Cristal Energético":
                nome = 'CE'
            elif item.type == "Metal Raro":
                nome = 'MR'
            elif item.type == "Estrutura Antiga":
                if len(item.carregado_por) < 2:
                    return
                nome = 'EA'
            else:
                nome = 'I'
            item_removido = (nome + str(item.unique_id), item.pos)
            print(item_removido)
            print(self.recursos)
            if item_removido in self.recursos:
                self.recursos.remove(item_removido)
            
    def atualizar_agent_pos(self, agent):
        nome = agent.nome
        pos = agent.pos
        self.agentes_pos[nome] = pos

    def adicionar_contribuicao(self, item):
        if item != None:
            self.quant_entregue += 1
            self.contribuicao += item.pontos
        #pass

    def posicao_item(self, item_nome):
        for recurso in self.recursos:
            if recurso[0] == item_nome:
                return recurso[1]
        return None

    def step(self):
        print(self.recursos)
        #pass

def visualize_model(ax, model, step_number, pasta_save, save, salvar=False):
    # Cria uma matriz vazia para representar o grid
    grid = np.full((model.grid.width, model.grid.height), "", dtype=object)

    # Mark destination
    dx, dy = model.base
    grid[dx, dy] = "B "

    # Add all agents to the grid
    for agent in model.schedule.agents:
        x, y = agent.pos
        agent_class = type(agent).__name__
        print(f"Agent {agent.unique_id} at position ({x}, {y}) is of class {agent_class}")

        if isinstance(agent, ReativoSimples) or isinstance(agent, AgentEstados) or isinstance(agent, AgenteBaseadoEmObjetivos2) or isinstance(agent, AgenteCooperativo):
            nome = agent.nome

            if agent.has_item:
                item_carregado = agent.item
                if item_carregado.type == "Cristal Energético":
                    grid[x, y] += f"{nome}{agent.unique_id}(CE{item_carregado.unique_id})"
                elif item_carregado.type == "Metal Raro":
                    grid[x, y] += f"{nome}{agent.unique_id}(MR{item_carregado.unique_id})"
                elif item_carregado.type == "Estrutura Antiga":
                    grid[x, y] += f"{nome}{agent.unique_id}(EA{item_carregado.unique_id})"
                else:
                    grid[x, y] += f"{nome}{agent.unique_id}(I{item_carregado.unique_id})"
            else:
                grid[x, y] += f"{nome}{agent.unique_id} "
        elif isinstance(agent, AgentBDI):
            nome = agent.nome + str(agent.unique_id)
            
            grid[x, y] += f"{nome}"

    # Add single items to the grid
    for item in model.items_cristal:
        if not item.carregado_por:
            x, y = item.pos
            grid[x, y] += f"CE{item.unique_id} "

    for item in model.items_metal:
        if not item.carregado_por:
            x, y = item.pos
            grid[x, y] += f"MR{item.unique_id} "

    for item in model.items_estrutura:
        if not item.carregado_por:
            x, y = item.pos
            grid[x, y] += f"EA{item.unique_id} "

    # Atualiza o conteúdo do eixo
    ax.clear()  # Limpa o eixo para a próxima atualização
    for x in range(model.grid.width):
        for y in range(model.grid.height):
            ax.text(y, x, grid[x, y], ha='center', va='center', color='white', fontsize=12,
                    bbox=dict(facecolor='gray', edgecolor='white', boxstyle='round,pad=0.3'))

    ax.set_xlim(-0.5, model.grid.width - 0.5)
    ax.set_ylim(-0.5, model.grid.height - 0.5)
    ax.set_xticks(range(model.grid.width))
    ax.set_yticks(range(model.grid.height))
    ax.grid()
    ax.set_title(f'Step {step_number}')
    fig.savefig(os.path.join(os.path.join(pasta_save, save), f"resultado_step{step_number}"))

class RandomWalkModel(Model):
    def __init__(self, agents, width, height, num_cristais, num_metais, num_estrutura_old, base, seed=None, tem_bdi=False):
        super().__init__()  # Inicializa o Model base
        self.num_reativosSimples = agents['agenteSimples']
        self.num_agentsEstados = agents['agenteEstado']
        self.num_agentesObjetivos = agents['agenteObjetivo']
        self.num_agentesCooperativos = agents['agenteCooperativo']
        self.grid = MultiGrid(width, height, False)
        self.random = random.Random(seed)
        self.schedule = SimultaneousActivation(self)
        self.num_metais = num_metais
        self.num_cristais = num_cristais
        self.num_estrutura_old = num_estrutura_old
        self.base = base
        self.items_metal = []
        self.items_cristal = []
        self.items_estrutura = []
        self.contribuicao_total = 0
        self.quant_entregue_total = 0
        self.memoria_compartilhadaAgenteObjetivo = []
        self.tem_bdi = tem_bdi
        if tem_bdi:
            self.bdi = AgentBDI(self)
        # Criando os agentes Reativos simples
        for i in range(self.num_reativosSimples):
            a = ReativoSimples(self)
            self.schedule.add(a)
            self.grid.place_agent(a, base)

        # Criando os agentes baseados em estados
        for i in range(self.num_agentsEstados):
            a = AgentEstados(self)
            self.schedule.add(a)
            self.grid.place_agent(a, base)

        # Criando os agentes baseados em objetivos
        for i in range(self.num_agentesObjetivos):
            a = AgenteBaseadoEmObjetivos2(self)
            self.schedule.add(a)
            self.grid.place_agent(a, base)

        # Criando os agentes baseados em objetivos
        for i in range(self.num_agentesCooperativos):
            a = AgenteCooperativo(self)
            self.schedule.add(a)
            self.grid.place_agent(a, base)

        # Criando os metais raros
        for i in range(self.num_metais):
            s = Item(self, "Metal Raro", 20)
            self.items_metal.append(s)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(s, (x, y))

        # Criando os cristais
        for i in range(self.num_cristais):
            s = Item(self, "Cristal Energético", 10)
            self.items_cristal.append(s)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(s, (x, y))

        # Criando as estruturas antigas
        for i in range(self.num_estrutura_old):
            d = Item(self, "Estrutura Antiga", 50)
            self.items_estrutura.append(d)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(d, (x, y))
        
        if tem_bdi:
            self.schedule.add(self.bdi)
            self.grid.place_agent(self.bdi, base)

    def step(self):
        self.schedule.step()

    def remove_item(self, item):
        if item is not None:
            self.contribuicao_total += item.pontos
            self.quant_entregue_total += 1
            self.bdi.adicionar_contribuicao(item)
            if item.type == "Cristal Energético":
                self.items_cristal.remove(item)
            elif item.type == "Metal Raro":
                self.items_metal.remove(item)
            elif item.type == "Estrutura Antiga":
                self.items_estrutura.remove(item)
            self.grid.remove_agent(item)

    def obter_estado_grid(self):
        """
        Retorna uma lista de todos os itens no grid, incluindo suas posições e tipos.
        """
        estado_grid = []
        # Iterando diretamente sobre o grid com os índices x, y
        for x in range(self.grid.width):  # A largura do grid
            for y in range(self.grid.height):  # A altura do grid
                # Obtém todos os objetos presentes na célula (x, y)
                cell_contents = self.grid.get_cell_list_contents((x, y))  # Passa a tupla diretamente
                for obj in cell_contents:
                    if isinstance(obj, Item):  # Verifica se o objeto é do tipo Item
                        estado_grid.append({
                            'posicao': (x, y),
                            'tipo': obj.type,
                            'pontos': obj.pontos
                        })
        return estado_grid


# Parameters
agents = { 'agenteEstado': 0, 'agenteSimples': 0, 'agenteObjetivo': 2, 'agenteCooperativo': 2 }
width = 11
height = 11
num_cristais = 4
num_metais = 5
num_estruturas_old = 4
num_steps = 45
tempo_espera = 0.5
base = (5, 5)
MEMORIA_COMPARTILHADA_AGENTES_ESTADO = np.full((width, height), "Desconhecido", dtype=object)
run = verificar_save_name(pasta_save, "teste_agentesObjetivo")

# Create the model
model = RandomWalkModel(agents, width, height, num_cristais, num_metais, num_estruturas_old, base, tem_bdi=True)


# Define o loop principal do modelo
fig, ax = plt.subplots(figsize=(10, 10))  # Cria a figura e o eixo fora da função
plt.ion()  # Ativa o modo interativo
visualize_model(ax, model, " inicial", pasta_save= pasta_save, save= run, salvar=True)
for step in range(num_steps):
    print(f"###############step{step}###############")
    model.step()  # Realiza o próximo passo no modelo
    visualize_model(ax, model, step, pasta_save= pasta_save, save= run, salvar=True)  # Atualiza a mesma janela
    plt.pause(tempo_espera)  # Aguarda 0.5 segundo antes da próxima atualização

time.sleep(5)
plt.ioff()  # Desativa o modo interativo
plt.close()  # Fecha automaticamente a janela




print(f"\n\n\n \tContribuição total: {model.contribuicao_total}")
print(f"\tcontribuição total em quantidade: {model.quant_entregue_total}")
for agent in model.schedule.agents:
    #if isinstance(agent,ReativoSimples):
    nome = agent.nome
    print(f" \tContribuição do agente {nome}{agent.unique_id}: {agent.contribuicao}")
    print(f" \tContribuição do agente quantidade {nome}{agent.unique_id}: {agent.quant_entregue}")



    # Tá demorando um passo só para pegar o item == ok
    # Não pegar item com peso 1 apenas == ok
    # Visualizar contribuições == é só fechar janela
