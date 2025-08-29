package common

import (
	"bufio"
	"strings" //since used in main i use same library
)


const HeaderLength = 4 

type Bet struct {
	Nombre 			string
	Apellido 		string
	DNI      		string
	Nacimiento 		string
	Numero 			string
	Agencia			string
}

func getBets(scanner *bufio.Scanner, batchSize int)([]Bet, error, bool){
	var bets []Bet

	for len(bets) < batchSize && scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			continue
		}

		campos := strings.Split(line, ",")
		if len(campos) < 5 {
			continue // línea inválida
		}

		bet := Bet{
			Nombre:     campos[0],
			Apellido:   campos[1],
			DNI:        campos[2],
			Nacimiento: campos[3],
			Numero:     campos[4],
		}

		bets = append(bets, bet)
	}

	if err := scanner.Err(); err != nil {
		return nil, err, false
	}
	if len(bets) == 0 {
		return nil, nil,true //  true= EOF > fin de archivo
	}
	return bets,nil, false
}