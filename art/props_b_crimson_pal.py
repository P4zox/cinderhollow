"""Crimson Manor prop ramps (dark -> light), sampled from the region's good props (cm_portrait, cm_statue, cm_candelabra,
cm_sconce) and tiles_crimson. Shared by the batch-B crimson generators."""
from props_b_lib import ramp

WOOD = ramp('0c0608', '1a0e10', '2a1616', '3e2220', '56302a', '744634', '946048')          # lacquered mahogany
OAK = ramp('100a08', '1e140e', '2e2016', '42301f', '5a432a', '76593a', '957552')           # paler, worn wood (servants' rooms)
RED = ramp('16040a', '22060c', '360910', '4e0c16', '6c141c', '8e2026', 'b03634', 'd05a4a')    # velvet / wine
GILT = ramp('120d0a', '17110c', '2a2017', '3f3222', '54452f', '6c5a3c', '877148', 'a89060', 'd0b878')
IRON = ramp('08070c', '19181c', '2a282e', '3f3c44', '58545c', '77727a', '9a9498', 'bdb5b0')
STONE = ramp('0c0a10', '15131b', '1f1c27', '2a2733', '3c3946', '524e5c', '6c6878', '8c8898', 'aaa6b4')
BRICK = ramp('0e080a', '1c0e10', '2c1618', '3e2022', '542c2a', '6c3c36', '885046')
LINEN = ramp('1c1816', '2a2420', '4a4038', '6e6254', '968a78', 'bcb09a', 'ddd2bc')
PAPER = ramp('2a2420', '4a4038', '6e6254', '968a78', 'bcb09a', 'ddd2bc', 'efe6d2')
FLESH = ramp('140c10', '241820', '3a2a2e', '54403e', '725a52', '927866', 'b09682', 'cbb4a0')
BLACK = ramp('060509', '0c0a10', '141119', '1e1a24', '2a2531', '38323f')
HAIRB = ramp('1a140c', '2e2414', '4a3a20', '6a5630', '8c7442')                                # dim blond
FIRE = ramp('5a1808', 'b0400e', 'e2781c', 'ffb648', 'ffe7a4')
EMBER = ramp('1a0806', '3a0e08', '6a1a0a', 'a0300c', 'd8581a')
GLASSG = ramp('06100c', '0c1a16', '142a22', '1e3c30', '2e5444', '4a7a60')                    # bottle glass
CANVAS = ramp('0a0608', '120a0c', '1a0f10', '241515', '301c1a', '3e2620', '50322a')            # an old dark oil ground
GREEN = ramp('0a0e0a', '121a12', '1a2818', '24381e', '324a26', '465e32')                      # rose leaves
SKY = ramp('0c0a14', '161424', '221e36', '302a4a', '423a60')
OUTLIT = '1a0e10'   # the lit-side outline
