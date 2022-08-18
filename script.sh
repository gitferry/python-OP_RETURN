fee=0.00002
op1_data="42424e54e2b01873b2eb52d822b55f49ac0d22c6f42f7beab5ed6a6c64024d86c29218927206784aea788ec12f3252f6717c9e602b525106b7df4937ab16719114795cb9ab2a29b7fbe0"
utxo_txid="bfca4435ebbc38262b670cf11c14a69529db325ddcdd3de49e45093667516338"
utxo_vout=0
amount=0.01
outputs=$(cat utxo.json | jq -r '.outputs')
changeaddress=$(bitcoin-cli getrawchangeaddress)
rawtxhex=$(bitcoin-cli -named createrawtransaction inputs='''[ { "txid": "'$utxo_txid'", "vout": '$utxo_vout' } ]''' outputs='''{ "data": "'$op1_data'", "'$changeaddress'": 0.00998 }''')
address="bc1qjjzqeej4pzwg4aatxnenw54j3ewmmkwc04c8mn"
bitcoin-cli signrawtransactionwithwallet $rawtxhex $outputs
