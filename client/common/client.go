package common

import (
	"bufio"
	"fmt"
	"net"
	"time"
	"os"
	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

type Bet struct {
	Nombre 			string
	Apellido 		string
	DNI      		string
	Nacimiento 		string
	Numero 			string
}


// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// sendMessage handles secsure message sending (avoiding short-write)
func (c *Client)  sendMessage(msg string) error{ //	[ ] WiteFull ?
	msg_length := len([]byte(msg))
	sent := 0

	for sent < len(msg_length){
		n, err = c.conn.write(msg_length[sent:])
		if err != nil {
			return err
		}
		sent += n
	}

	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(sigChan chan os.Signal) {
		for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
			select {
			case  <-sigChan:
            	log.Infof("action: exit | result: success | client_id: %v", c.config.ID)
            	if c.conn != nil {
            	    c.conn.Close()
            	}
            	return
			default:
				// Create the connection to the server in every loop iteration
				c.createClientSocket()

				bet := Bet{ //[ ] check if env variables in doker file,??
					Nombre: 		os.Getenv("NOMBRE")
					Apellido: 		os.Getenv("APELLIDO")
					DNI:			os.Getenv("DNI")
					Nacimiento:		os.Getenv("NACIMIENTO")
					Numero:			os.Getenv("NUMERO")
				}

				//serialize https://pkg.go.dev/fmt#Sprintf
				message := fmt.Sprintf("%s|%s|%s|%s|%s", bet.Nombre, bet.Apellido, bet.DNI, bet.Nacimiento, bet.Numero)

				if err := c.sendMessage(message); err != nil {
					log.Errorf("action: apuesta_enviada | result: fail | dni: %v | numero: %v | error: %v", bet.DNI, bet.Numero, err)
            	    c.conn.Close()
					return
				}

				//read confirmation https://pkg.go.dev/bufio#Reader
				resp, err = bufio.NewReader(c.conn).ReadString("\n")
				c.conn.Close()

				if err!= nil {
					log.Errorf("action: apuesta_almacenada | result: fail | dni: %v | numero: %v | error: %v", bet.DNI, bet.Numero, err)
				}
				
				log.Infof("action: apuesta_almacenada | result: success | dni: %v | numero: %v", bet.DNI, bet.Numero)
				time.Sleep(c.config.LoopPeriod)
			}
		}
		log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)

}
