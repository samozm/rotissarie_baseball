R = sorted([1174,1136,1067,1006,1241,1110,974,997,1159,966,898],reverse=True)
HR = sorted([433,352,353,284,382,321,291,332,355,302,260],reverse=True)
RBI = sorted([1198,1088,1077,1030,1147,1016,955,1000,1075,905,897],reverse=True)
SB = sorted([113,141,97,106,94,110,127,121,123,73,72],reverse=True)
AVG = sorted([0.2735,0.2592,0.2740,0.2642,0.2768,0.2710,0.2620,0.2601,0.2705,0.2645,0.2641],reverse=True)
K = sorted([1643,1531,1788,1598,1330,1387,1480,1725,1132,1391,1336],reverse=True)
W = sorted([97,98,109,112,80,93,85,99,64,84,74],reverse=True)
SV = sorted([59,73,3,55,115,79,105,42,39,59,54],reverse=True)
ERA = sorted([3.907, 3.898,4.144,3.665,4.444,4.107,3.760,4.217,3.493,4.112,4.616])
WHIP = sorted([1.216,1.244,1.262,1.102,1.339,1.247,1.210,1.291,1.131,1.267,1.284])

print("R, HR, RBI, SB, AVG, K, W , SV, ERA, WHIP")
for i in range(len(R)):
    print(R[i],HR[i],RBI[i],SB[i],AVG[i],K[i],W[i],SV[i],ERA[i],WHIP[i])