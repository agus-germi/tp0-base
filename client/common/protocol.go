package common
import (
	"fmt"
	"strings"
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