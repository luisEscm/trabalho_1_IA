import matplotlib.pyplot as plt
import numpy as np
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
import random
import time


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

    # Movimenta no eixo X em direção à base, se necessário
    if x_atual < x_base:
        return (x_atual + 1, y_atual)
    elif x_atual > x_base:
        return (x_atual - 1, y_atual)

    # Movimenta no eixo Y em direção à base, se necessário
    if y_atual < y_base:
        return (x_atual, y_atual + 1)
    elif y_atual > y_base:
        return (x_atual, y_atual - 1)

    # Se já estiver na base, mantém a posição
    return posicao_atual

class ReativoSimples(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.has_item = False
        self.item = None
        self.contribuicao = 0
        self.quant_itens_entregues = 0
        self.nome = "AR"

    def pegar_item(self, item):
        if item.type == "Cristal Energético" or item.type == "Metal Raro":
            self.has_item = True
            self.item = item
            item.carregado_por = [self]

    def entregar_item(self):
        if self.item:
            self.contribuicao += self.item.pontos
            self.quant_itens_entregues += 1

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
            if passo is not None:
                new_position = passo
            elif self.has_item:  # Se o agente estiver carregando um item
                # Chama a função para determinar o próximo passo no caminho para a base
                new_position = caminho_para_destino(self.pos, self.model.base, self.model.grid) #base
            else:
                # Caso contrário, o agente escolhe um passo aleatório (comportamento padrão)
                new_position = self.random.choice(possible_steps)

            self.model.grid.move_agent(self, new_position)

            if not self.has_item and item is not None:
                self.pegar_item(item)


        if self.pos == self.model.base:
            self.entregar_item()

class AgentEstados(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.has_item = False
        self.item = None
        self.contribuicao = 0
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
                #print('1:', item, passo)
                # Atualiza a memória se encontrar um item
                if item is not None:
                    MEMORIA_COMPARTILHADA_AGENTES_ESTADO[item.pos[0]][item.pos[1]] = "Item"

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

class AgenteBaseadoEmObjetivos(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.has_item = False
        self.item = None
        self.contribuicao = 0
        self.nome = "ABO"
        self.conhece_itens = []  # Inicializa a lista de itens conhecidos vazia
        self.emBuscaPor = None

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

def visualize_model(ax, model, step_number):
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

        if isinstance(agent, ReativoSimples) or isinstance(agent, AgentEstados) or isinstance(agent, AgenteBaseadoEmObjetivos):
            nome = agent.nome

            if agent.has_item:
                item_carregado = agent.item
                if item_carregado.type == "Cristal Energético":
                    grid[x, y] += f"{nome}{agent.unique_id}(CE)"
                elif item_carregado.type == "Metal Raro":
                    grid[x, y] += f"{nome}{agent.unique_id}(MR)"
                elif item_carregado.type == "Estrutura Antiga":
                    grid[x, y] += f"{nome}{agent.unique_id}(EA)"
                else:
                    grid[x, y] += f"{nome}{agent.unique_id}(I)"
            else:
                grid[x, y] += f"{nome}{agent.unique_id} "

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

class RandomWalkModel(Model):
    def __init__(self, agents, width, height, num_cristais, num_metais, num_estrutura_old, base, seed=None):
        super().__init__()  # Inicializa o Model base
        self.num_reativosSimples = agents['agenteSimples']
        self.num_agentsEstados = agents['agenteEstado']
        self.num_agentesObjetivos = agents['agenteObjetivo']
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
        self.memoria_compartilhadaAgenteObjetivo = []

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
            a = AgenteBaseadoEmObjetivos(self)
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

    def step(self):
        self.schedule.step()

    def remove_item(self, item):
        if item is not None:
            self.contribuicao_total += item.pontos
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
agents = { 'agenteEstado': 0, 'agenteSimples': 0, 'agenteObjetivo': 1 }
width = 6
height = 6
num_cristais = 1
num_metais = 0
num_estruturas_old = 4
num_steps = 20
base = (0, 0)
MEMORIA_COMPARTILHADA_AGENTES_ESTADO = np.full((width, height), "Desconhecido", dtype=object)

# Create the model
model = RandomWalkModel(agents, width, height, num_cristais, num_metais, num_estruturas_old, base)


# Define o loop principal do modelo
fig, ax = plt.subplots(figsize=(10, 10))  # Cria a figura e o eixo fora da função
plt.ion()  # Ativa o modo interativo

for step in range(num_steps):
    visualize_model(ax, model, step)  # Atualiza a mesma janela
    plt.pause(1)  # Aguarda 0.5 segundo antes da próxima atualização
    model.step()  # Realiza o próximo passo no modelo

time.sleep(5)
plt.ioff()  # Desativa o modo interativo
plt.close()  # Fecha automaticamente a janela




print(f"\n\n\n \tContribuição total: {model.contribuicao_total}")
for agent in model.schedule.agents:
    #if isinstance(agent,ReativoSimples):
    nome = agent.nome
    print(f" \tContribuição do agente {nome}{agent.unique_id}: {agent.contribuicao}")



    # Tá demorando um passo só para pegar o item == ok
    # Não pegar item com peso 1 apenas == ok
    # Visualizar contribuições == é só fechar janela
