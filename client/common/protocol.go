package common
import (
	"fmt"
	"strings"
	"bufio"
)

// serializeBet returns serialized payload
func serializeBet(bet Bet, client_id string ) string {
	return fmt.Sprintf("%s|%s|%s|%s|%s|%s",
		bet.Nombre, bet.Apellido, bet.DNI, bet.Nacimiento, bet.Numero, client_id,
	)
}

// validateAck checks if the server response matches the expected "ACK".
func validateAck(resp string) bool {
	resp = strings.TrimSpace(resp)
	return resp == "ACK"
}

// serializeBatch joins bets into one message
func serializeBatch(bets []Bet, client_id string) string {
	records := make([]string, 0, len(bets))
	for _, bet := range bets {
		records = append(records, serializeBet(bet, client_id))
	}
	return strings.Join(records, ",")
}

// sendEnd send an END message to notify the server that this client has finished sending bets
func (c *Client) sendEnd() error {
	endMessage := fmt.Sprintf("END|%v\n", c.config.ID)
	if err := c.sendMessage(endMessage); err != nil {
		return fmt.Errorf("action: send_end | result: fail | client_id: %v | error: %w", c.config.ID, err)
	}
	return nil
}

// waitForWinners waits for and collect the list of winners from the server until WINNERS_END is received
func (c *Client) waitForWinners() error {
	log.Infof("action: consulta_ganadores | result: in_progress | client_id: %v", c.config.ID)
	reader := bufio.NewReader(c.conn)
	var allWinners []string

	for {
		msg, err := reader.ReadString('\n')
		if err != nil {
			log.Errorf("action: consulta_ganadores | result: fail | err: %v", err)
		}
		msg = strings.TrimSpace(msg)	
		if msg == "WINNERS_END" {break}
		if msg != "" {allWinners = append(allWinners, msg)}

	}
	log.Infof("action: consulta_ganadores | result: success | client_id: %v | cant_ganadores: %v",c.config.ID, len(allWinners))
	return nil
}