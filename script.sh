fee=0.0001
op1_data="42424e54e2b01873b2eb52d822b55f49ac0d22c6f42f7beab5ed6a6c64024d86c29218927206784aea788ec12f3252f6717c9e602b525106b7df4937ab16719114795cb9ab2a29b7fbe0"
op2_data="42424e54abb6b78024f0bf67c0146b305a274a71b42cfbcfe57b634300a02b43729cb9c2303dd9ba32d4f37acad683eb9b1ae0e3bab74701545f17b8fea3"
bitcoin-cli listunspent | jq 'sort_by(.amount) | reverse' > unspents.json
utxo_txid=$(cat unspents.json | jq -r '.[0] | .txid')
utxo_vout=$(cat unspents.json | jq -r '.[0] | .vout')
amount=$(cat unspents.json | jq -r '.[0] | .amount')
coins=$((amount-fee))
changeaddress=$(bitcoin-cli getrawchangeaddress)
rawtxhex=$(bitcoin-cli -named createrawtransaction inputs='''[ { "txid": "'$utxo_txid'", "vout": '$utxo_vout' } ]''' outputs='''{ "data": "'$op1_data'", "'$changeaddress'": 0.026 }''')
echo $rawtxhex
