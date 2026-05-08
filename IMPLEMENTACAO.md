# Documentação da Implementação

## Visão geral

Implementei um sistema de recompensas sobre a API de locação existente e tratei
essa funcionalidade como parte do fluxo principal do produto, não como um bloco
isolado.

Na prática, a entrega final inclui:

- concessão automática de pontos no retorno da locação
- resumo de rewards por cliente
- histórico de transações
- resgate de pontos com desconto aplicado na locação
- tiers de fidelidade com multiplicadores
- endpoint de detalhe da transação com os detalhes completos do cálculo realizado
- autenticação com JWT
- controle de acesso por papel
- documentação OpenAPI com Swagger e ReDoc
- collection do Postman cobrindo cenários positivos, negativos e edge cases
- um `AGENTS.md` com as regras de engenharia e manutenção seguidas no projeto

Além de fechar os requisitos principais, eu também aproveitei para melhorar a
qualidade estrutural do projeto, principalmente em arquitetura, testes,
documentação e previsibilidade de comportamento.

## Principais decisões de design

### Sistema de rewards baseado em ledger

O sistema de rewards foi modelado com base em um ledger transacional.

Em vez de manter um saldo mutável persistido no cliente, escolhi centralizar a
solução em `RewardTransaction`, de forma que o saldo atual seja derivado do
histórico de transações.

Cada transação registra:

- cliente
- snapshot do email do cliente
- locação relacionada
- tipo da transação (`earned` ou `redeemed`)
- valor de pontos com sinal
- motivo legível
- um campo opcional com detalhes do cálculo que originou a transação
- `idempotency_key` opcional
- timestamp

Essa decisão me pareceu a melhor para o teste porque:

- evita dessincronização entre saldo e histórico
- melhora a auditabilidade
- deixa o comportamento mais transparente
- simplifica o raciocínio sobre ganhos e resgates

Não transformei isso em um sistema de dupla entrada ou algo mais contábil
porque seria um nível de complexidade desnecessário para o escopo da avaliação.

### Separação entre views, services e repositories

Mantive a aplicação organizada com separação explícita de responsabilidades:

- views lidam com HTTP, serialização e formatação de resposta
- services concentram regras de negócio e orquestração
- repositories são o único lugar em que consultas ORM são executadas

Essa estrutura ficou especialmente importante depois que rewards, rentals,
visibilidade, exportação e controle de acesso começaram a se cruzar. Se essa
lógica ficasse espalhada em views, o código ficaria mais difícil de testar,
mais repetitivo e mais frágil a regressões.

Também usei essa oportunidade para reforçar uma regra arquitetural que considero
valiosa: o acesso ao banco não deve vazar para camadas de HTTP.

### Formalização das regras em `AGENTS.md`

Além do código em si, criei um `AGENTS.md` para registrar de forma explícita as
regras de engenharia adotadas no repositório.

Esse arquivo funciona como uma referência de trabalho para agentes de IA e para
qualquer pessoa que faça manutenção no projeto depois, deixando claro:

- como a arquitetura está organizada
- onde regras de negócio devem ficar
- onde consultas ORM podem existir
- quais validações precisam continuar verdes
- quais padrões de documentação e testes devem ser mantidos

A intenção foi reduzir ambiguidade e evitar que futuras alterações desviem do
padrão que foi consolidado aqui. Também considero importante que esse arquivo
seja atualizado sempre que alguma convenção estrutural do projeto mudar.

### Integração do ganho de pontos no retorno da locação

O ponto de integração escolhido para a concessão automática foi o retorno da
locação.

Isso faz sentido porque:

- o status de devolução pontual só é conhecido no retorno
- a locação só está realmente concluída nesse momento
- a regra de negócio pertence ao domínio da locação e rewards, não à view

### Histórico compacto e detalhe rico

Eu não expus todos os detalhes de cálculo nas listagens de histórico.

A decisão foi:

- endpoints de histórico retornam transações compactas
- o endpoint de detalhe da transação mostra o contexto completo de cálculo,
  como bônus aplicados, multiplicador de tier ou desconto gerado no resgate

Fiz isso para manter os endpoints de lista mais leves, mais legíveis e mais
previsíveis para consumo. O endpoint de detalhe vira a fonte principal de
auditoria quando o consumidor realmente precisa entender o cálculo.

### UUID v7 como chave primária

Todos os modelos usam `UUIDField` com `default=uuid7` em vez de `BigAutoField`.

UUIDs v7 são **monotônicos por tempo**: o prefixo de 48 bits é o timestamp Unix em
milissegundos, então registros inseridos em sequência ficam fisicamente próximos
no índice B-tree. Isso elimina o problema clássico de UUID v4, onde inserts
aleatórios causam page splits e fragmentação de índice.

Em relação a autoincrement inteiro:

- sem enumeração: IDs inteiros expõem volume de dados e permitem varredura trivial
- sem acoplamento com o banco: o ID pode ser gerado na aplicação antes do insert,
  o que simplifica testes, importações e APIs que precisam do ID antes do commit
- federação natural: IDs gerados em instâncias diferentes nunca colidem

O tradeoff é espaço em disco e overhead de índice, ambos irrelevantes no porte desta
aplicação.

### Expansão da composição de preço em locações

Para suportar rewards de forma limpa, expandi a modelagem de preço da locação.

O rental passou a trabalhar com:

- `subtotal`
- `duration_discount`
- `reward_discount`
- `total_cost`
- `late_fee`

Isso ajuda em dois pontos:

- explicar melhor como o total foi calculado
- permitir que descontos de rewards convivam com descontos de duração e multa de atraso

### Controle de acesso e visibilidade

O projeto original era mais simples nessa parte, então ampliei o controle de
acesso para dar previsibilidade melhor ao comportamento da API.

O desenho final ficou assim:

- endpoints públicos: catálogo de carros, health e documentação
- clientes autenticados: apenas seus próprios rentals e rewards
- staff: visões cross-customer, rotas administrativas e relatórios

Em alguns casos, preferi responder `404` em vez de `403` quando um cliente tenta
acessar um recurso de outro cliente. Fiz isso para evitar confirmação
desnecessária da existência do recurso.

O exemplo mais claro disso é o detalhe de rental:

- admin vê qualquer rental
- cliente comum vê apenas os próprios
- rental alheio para cliente comum retorna `404`

### Visibilidade coerente de carros indisponíveis

Havia uma inconsistência entre listagem e detalhe de carros.

Corrigi isso com a seguinte regra:

- público vê apenas carros disponíveis
- detalhe público de carro indisponível retorna `404`
- staff pode listar carros indisponíveis com `include_unavailable=true`
- staff pode detalhar carros indisponíveis

Isso deixa o contrato mais coerente entre listagem e detalhe e evita exposição
operacional desnecessária para usuários comuns.

## O que foi implementado além do mínimo

Além do núcleo de rewards, a solução final inclui melhorias que não eram
estritamente necessárias para cumprir o mínimo, mas que elevam a qualidade da
entrega:

- autenticação JWT
- escopo de acesso por cliente/staff
- tiers Bronze, Silver e Gold
- multiplicadores por tier
- resgate de pontos
- export CSV/PDF
- paginação e filtros
- docstrings voltadas ao consumidor da API
- schema OpenAPI consistente
- collection Postman com cenários amplos
- Django admin mais útil para fluxo operacional
- endpoint de detalhe de rental

## O que eu decidi não colocar

Também houve decisões conscientes sobre o que não adicionar.

### Não persistir saldo mutável no cliente

Como a base foi um ledger, não criei um campo separado de saldo atual no
cliente. Preferi derivar o saldo a partir do histórico.

### Não transformar rewards em contabilidade completa

Não implementei uma estrutura de dupla entrada ou um sistema contábil mais
formal, porque seria muito mais complexo do que o necessário para a proposta do
teste.

### Não expor todos os detalhes de cálculo em endpoints de lista

Preferi manter o histórico compacto e delegar o detalhamento completo ao
endpoint de transação individual.

### Não tratar o resgate como operação idempotente

Mantive o comportamento de resgate sem uma `idempotency_key` obrigatória,
porque a leitura final do escopo aqui foi permitir múltiplos resgates válidos
quando disparados de forma intencional.

## Decisões de qualidade e manutenção

### Tipagem e toolchain

Alinhei o projeto ao ecossistema Astral:

- `uv`
- `ruff`
- `ty`

Também deixei o repositório com validações verdes e cobertura total.

### Testes organizados por app

Reorganizei a suíte para que cada app tenha seus próprios testes e seu próprio
`conftest.py`, em vez de concentrar tudo em um único lugar. Isso melhora
navegação e deixa mais claro o que pertence a cada contexto de domínio.

### Django admin tratado como parte do produto

Fiz algumas melhorias no admin porque, na prática, ele também é uma interface
de operação:

- histórico de rewards totalmente read-only
- link entre reward transaction e rental
- criação de rental no admin usando o mesmo service da API
- autocomplete e filtros melhores para customer e car
- bloqueio de campos sem sentido no add de rental

## Como validar a implementação

Os principais comandos que usei para validar a entrega foram:

```bash
uv run --with ruff ruff check .
uv run --with ty ty check .
uv run --with pytest --with pytest-django --with pytest-cov python -m pytest --cov=core --cov=cars --cov=customers --cov=rentals --cov=rewards --cov-report=term-missing -q -s
uv run python manage.py spectacular --file /tmp/schema.yaml
```

Eles validam, respectivamente:

- lint e consistência estática
- tipagem
- comportamento + cobertura
- geração do schema OpenAPI

## Premissas adotadas

Alguns pontos exigiram interpretação e eu optei por documentar as premissas:

- rewards devem funcionar como ledger append-only
- usuários comuns não devem conseguir inferir a existência de recursos alheios
- catálogo público deve esconder carros indisponíveis de forma consistente
- history endpoints devem ser compactos e o detalhe completo deve ficar no endpoint dedicado

## O que eu melhoraria com mais tempo

Se eu tivesse mais tempo, eu focaria mais em refinamento operacional do que em
novas funcionalidades.

Os próximos passos que eu priorizaria seriam:

- pipeline de CI com os mesmos gates locais
- exemplos mais ricos no OpenAPI
- abstração mais formal para exportadores CSV/PDF
- testes de concorrência mais profundos em fluxos críticos
- refinamentos extras na UX do admin
