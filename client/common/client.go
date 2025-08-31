package common

import (
	"bufio"
	"fmt"
	"net"
	"time"
	"os"
	"github.com/op/go-logging"
	"strings" //usado en main
)

var log = logging.MustGetLogger("log")


// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	BatchSize	  int
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
	bets 	[]Bet
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

// avisa que no hay más apuestas
func (c *Client) sendEnd() error {
	endMessage := fmt.Sprintf("END|%v\n", c.config.ID)
	if err := c.sendMessage(endMessage); err != nil {
		return fmt.Errorf("action: send_end | result: fail | client_id: %v | error: %w", c.config.ID, err)
	}
	return nil
}

// sendHeader
func(c*Client) sendHeader(length int) error {
    
	header := []byte{
        byte(length >> 24),
        byte(length >> 16),
        byte(length >> 8),
        byte(length),
    }

	sent := 0
    for sent < HeaderLength {
        n, err := c.conn.Write(header[sent:])
        if err != nil {
            return err
        }
        sent += n
    }
	return nil
}

// sendMessage handles secsure message sending (avoiding short-write)
func (c *Client)  sendMessage(msg string) error{ 
    msgBytes := []byte(msg)
	total := len(msgBytes)
	sent := 0

	if err := c.sendHeader(total); err != nil {
        log.Errorf("action: header_sent | result: fail | error: %v", err)
        return err
    }

	for sent < total {
		n, err := c.conn.Write(msgBytes[sent:])
		if err != nil {
			return err
		}
		sent += n
	}
	return nil
}


// queda escuchando ganadores del server
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

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(sigChan chan os.Signal) {
		
	file, err := os.Open(fmt.Sprintf("bets.csv"))
	if err != nil {
    	log.Errorf("action: open_csv | result: fail | client_id: %v | error: %v", c.config.ID, err)
    	return
    }
    defer file.Close()
    scanner := bufio.NewScanner(file)

	c.createClientSocket(); err != nil {
        log.Errorf("action: create_socket | result: fail | client_id: %v | error: %v", c.config.ID, err)
        return
    }
	defer c.conn.Close() // me aseguro que la conexion se cierre https://go.dev/tour/flowcontrol/12
	for{
        select {
        case <-sigChan:
            log.Infof("action: exit | result: success | client_id: %v", c.config.ID)
            return
        default:
        }
		//leo bet batch
		batch, err, eof := getBets(scanner, c.config.BatchSize)
		if eof {
			if err := c.sendEnd(); err != nil {
				log.Errorf("action: send_end | result: fail | client_id: %v | error: %v", c.config.ID, err)
			}
			if err := c.waitForWinners(); err != nil {
				log.Errorf("action: wait_winners | result: fail | client_id: %v | error: %v", c.config.ID, err)
			}
			return
		}else if err != nil{
			log.Errorf("action: read_batch | result: fail | error: %v", err)
		}
		
		var records []string
		for _, bet := range batch {
		    record := bet.Nombre + "|" + bet.Apellido + "|" + bet.DNI + "|" +
		              bet.Nacimiento + "|" + bet.Numero + "|" + c.config.ID
		    records = append(records, record)
		}

		message := strings.Join(records, ",")

		//envio payload
		if err := c.sendMessage(message); err != nil {
            log.Errorf("action: batch_sent | result: fail | error: %v", err)
            return
        }
		
		log.Infof("action: batch_sent | result: success | cantidad: %v", len(batch))

		//read confirmation https://pkg.go.dev/bufio#Reader
		_, err = bufio.NewReader(c.conn).ReadString('\n')

	}

	c.conn.Close()
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)


}
